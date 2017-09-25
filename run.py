from PIL import Image, ImageDraw
from selenium import webdriver
import os
import sys
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC

class ScreenAnalysis:
    driver = None
    config = None

    def __init__(self):
      self.set_config()
      self.set_up()
      self.capture_screens()
      self.clean_up()

    def set_config(self):
      with open('babyName.json') as data_file:
        self.config = json.load(data_file)

    def set_up(self):
      phantom_settings = dict(webdriver.DesiredCapabilities.PHANTOMJS)
      phantom_settings['phantomjs.page.settings.userAgent'] = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')
      phantom_settings['phantomjs.page.settings.javascriptEnabled'] = True,
      phantom_settings['phantomjs.page.settings.loadImages'] = True,
      phantom_settings['phantomjs.page.browserName'] = 'Google Chrome'

      self.driver = webdriver.PhantomJS(desired_capabilities=phantom_settings, service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'])

    def clean_up(self):
      self.driver.close()

    def get_screenshot_path(self, file_name):
      return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'screenshots', file_name)

    def capture_screens(self):
      for path in self.config['paths']:
        files = []
        for domain in self.config['domains']:
          url = domain['host'] + path['path']
          file_name = domain['name'] + '_' + path['name'] + '.png'
          self.screenshot(url, file_name)
          files.append(file_name)
        self.analyze(files, path['name'])

    def screenshot(self, url, file_name):
      print("Capturing", url, "screenshot as", file_name, "...")
      self.driver.set_window_size(1024, 768)
      self.driver.get(url)
      self.driver.save_screenshot(self.get_screenshot_path(file_name))
      self.driver.get_screenshot_as_png()
      print("Done.")

    def analyze(self, files, path_name):
      screenshot_staging = Image.open(self.get_screenshot_path(files[0]))
      screenshot_production = Image.open(self.get_screenshot_path(files[1]))
      columns = 60
      rows = 80
      screen_width, screen_height = screenshot_staging.size

      block_width = ((screen_width - 1) // columns) + 1 # this is just a division ceiling
      block_height = ((screen_height - 1) // rows) + 1

      for y in range(0, screen_height, block_height+1):
        for x in range(0, screen_width, block_width+1):
          region_staging = self.process_region(screenshot_staging, x, y, block_width, block_height)
          region_production = self.process_region(screenshot_production, x, y, block_width, block_height)

          if region_staging is not None and region_production is not None and region_production != region_staging:
            draw = ImageDraw.Draw(screenshot_staging)
            draw.rectangle((x, y, x+block_width, y+block_height), outline = "red")

      screenshot_staging.save("results/" + path_name + ".png")

    def process_region(self, image, x, y, width, height):
      region_total = 0

      # This can be used as the sensitivity factor, the larger it is the less sensitive the comparison
      factor = 100

      for coordinateY in range(y, y+height):
        for coordinateX in range(x, x+width):
          try:
            pixel = image.getpixel((coordinateX, coordinateY))
            region_total += sum(pixel)/4
          except:
            return

      return region_total/factor

ScreenAnalysis()