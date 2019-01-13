from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://google.com")

driver.find_element(By.ID, "q").send_keys("abc")

