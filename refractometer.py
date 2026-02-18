import glob
import time
import config
import signal
import asyncio
import numpy as np
import calibration
from smbus2 import SMBus

# Thermal Model Constants for 3mm PMMA wall
THERMAL_TAU = 150.0  # Seconds (Thermal lag)
GRADIENT_C = 0.18  # Heat loss to ambient air


class Refractometer:
    _instance = None
    _lock = asyncio.Lock()

    # ---------- Singleton Access ----------
    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                self = cls()
                await self._start_background_tasks()
                cls._instance = self
        return cls._instance


    def __init__(self):
        self.bus = SMBus(1)
        self.tmp0_addr = 0x40
        self.last_surf_temp = 20.0
        self.last_time = time.time()
        self.alcohol = 0.0
        self.sugar = 0.0
        self.salt = 0.0
        self.visual_alcohol = 0.0
        self.temp_ambient = 20.0
        self.temp_tube = 20.0
        self.temp_liquid = 20.0
        self.edge_pixel = 0.0

        self.coeffs_alcohol = self._generate_calibration_coeffs(calibration.calibration_data)
        self._tasks = []
        self._running = True


    # ---------- Background Task Control ----------
    async def _start_background_tasks(self):
        # self._tasks.append(asyncio.create_task(self.read_tmp006_die_temp()))
        # self._tasks.append(asyncio.create_task(self.read_ds18b20_ambient()))
        pass

    async def shutdown(self):
        print("Shutting down Refractometer...")
        self._running = False

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        try:
            self.bus.close()
        except:
            pass

        print("Refractometer stopped cleanly.")


    # ---------- Edge Detection ----------
    def _get_subpixel_edge(self, gray_img):
        """Parabolic interpolation for high-precision edge detection."""
        # Using ROI 340:360 from your sharp 'Image 3' turn
        roi_strip = gray_img[340:360, :]
        profile = np.mean(roi_strip, axis=0)
        grad = np.gradient(profile)
        peak_idx = np.argmax(grad)

        if 0 < peak_idx < len(grad) - 1:
            y1, y2, y3 = grad[peak_idx - 1:peak_idx + 2]
            denom = 2 * (y1 - 2 * y2 + y3)
            return peak_idx + (y1 - y3) / denom if denom != 0 else float(peak_idx)

        return float(peak_idx)


    def calculate(self, gray_img):
        """Calculates compensated concentrations for multiple substances."""
        # Non-Linear Concentration Mapping
        refined_idx = self._get_subpixel_edge(gray_img)
        self.read_tmp006_die_temp()
        self.read_ds18b20_ambient()
        # Apply polynomial: y = ax^3 + bx^2 + cx + d
        raw_alcohol = np.polyval(self.coeffs_alcohol, refined_idx)

        # Substance Mapping (Scale is Alcohol base)
        # Alcohol (v/v) factor to Brix is approx 1/0.55
        raw_brix = raw_alcohol / 0.55

        # Temperature Compensation (Ref: 20C)
        t_diff = self.temp_liquid - 20.0

        self.alcohol = max(0.0, round(raw_alcohol + (t_diff * 0.42), 2))  # Ethanol correction
        self.sugar = max(0.0, round(raw_brix + (t_diff * 0.062), 2))  # Sucrose correction
        self.salt = max(0.0, round(raw_brix + (t_diff * 0.062), 2))  # Sucrose correction
        self.visual_alcohol = max(0.0, round(raw_alcohol, 2))
        self.edge_pixel = max(0.0, round(refined_idx, 2))
        # return {
        #     "alcohol_vol": round(raw_alcohol + (t_diff * 0.42), 2),  # Ethanol correction
        #     "sugar_brix": round(raw_brix + (t_diff * 0.062), 2),  # Sucrose correction
        #     "salt_nacl": round(raw_brix + (t_diff * 0.062), 2),  # Sucrose correction
        #     "raw_alcohol_reading": round(raw_alcohol, 2),
        #     "refined_pixel_idx": round(refined_idx, 2),
        #     "temp_liquid_est": round(t_liq, 2),
        #     "temp_ambient": round(t_amb, 2),
        #     "temp_tube_surface": round(t_surf, 2)
        # }


    def read_tmp006_die_temp(self):
    # async def read_tmp006_die_temp(self):
        """Asynchronously Reads die temperature from TMP006 via I2C."""
        # while self._running:
        try:
            # Register 0x01 is Die Temp, standard 14-bit format
            raw = self.bus.read_word_data(self.tmp0_addr, 0x01)
            # Endian swap for Raspberry Pi
            val = ((raw << 8) & 0xFF00) | (raw >> 8)
            temp = (val >> 2) / 32.0 + config.TUBE_TEMPERATURE_CORRECTION_DEGC
        except Exception as e:
            print(f"TMP006 error: {e}")
            temp = 20.0

        self.temp_tube = max(0.0, round(temp, 2))
        now = time.time()
        dt = now - self.last_time
        slope = (self.temp_tube - self.last_surf_temp) / dt if dt > 0 else 0
        t_liq = self.temp_tube + (THERMAL_TAU * slope) + (GRADIENT_C * (self.temp_tube - self.temp_ambient))
        self.temp_liquid = max(0.0, round(t_liq, 2))

        self.last_surf_temp = self.temp_tube
        self.last_time = now

        # await asyncio.sleep(1)


    def read_ds18b20_ambient(self):
        # async def read_ds18b20_ambient(self):
        """Asynchronously Reads 1-wire ambient temperature sensor."""
        # while self._running:
        try:
            device_folder = glob.glob('/sys/bus/w1/devices/28*')  # TODO: replace address from config
            if len(device_folder) > 0:
                with open(device_folder[0] + '/w1_slave', 'r') as f:
                    lines = f.read()
                if "YES" in lines:
                    temp = float(lines.strip().split("t=")[-1]) / 1000.0 + config.AIR_TEMPERATURE_CORRECTION_DEGC
                    self.temp_ambient = max(0.0, round(temp, 2))
                else:
                    print('Ambient sensor not ready')
            else:
                print("Ambient sensor not found")
        except Exception as e:
            print(f"DS18B20 error: {e}")
            self.temp_ambient = 20.0

        # await asyncio.sleep(1)


    def _generate_calibration_coeffs(self, data_dict):
        """
        --- CALIBRATION CONSTANTS ---
        Coefficients for 3rd-order polynomial: Concentration = f(pixel_index)
        Pre-calculated once from your provided dataset
        P = (-1.082e-08)*x^3 + (5.421e-05)*x^2 + (-0.115)*x + 115.4
        COEFFS_ALCOHOL = np.array([-1.082e-08, 5.421e-05, -0.115, 115.4])
        """
        # Extract values into sorted arrays. Polyfit requires float arrays for precision
        y_percents = np.array(list(data_dict.keys()), dtype=float)
        x_pixels = np.array(list(data_dict.values()), dtype=float)

        # Fit a 3rd-degree polynomial for the non-linear "bulge"
        return np.polyfit(x_pixels, y_percents, 3)
