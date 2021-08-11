from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import csv 
from bs4 import BeautifulSoup
import requests
import os
from pathlib import Path
from lib.price_utils import getSkus, mergeSort, merge, wildCardDict
import pdb


class SFBot:
    def __init__(self, username, password, twoAuth, site):
        # Locate Chrome Driver
        home = str(Path.home())
        try:
            # Windows
            driver_loc = home + '\chromedriver'
            self.driver = webdriver.Chrome(driver_loc)
        except: 
            # Mac
            driver_loc = home + '/chromedriver'
            self.driver = webdriver.Chrome(driver_loc)
            
        # Set implicit wait time
        self.driver.implicitly_wait(5)
        
        # Maximize window
        self.driver.maximize_window()
        
        # Secrets
        self.username = username
        self.password = password
        self.twoAuth = twoAuth
        self.site = site
        
        # CSV File for Category Mapping
        csv_folder = Path("csv/")
        file_to_open = csv_folder / ("categories_" + self.site + ".csv")
        self.category_csv = file_to_open
        
        # Go to login site
        self.driver.get("https://staging-eu01-lululemon.demandware.net/on/demandware.store/Sites-Site/default/ViewLogin-StartAM")
        self.driver.find_element_by_xpath("//button[contains(text(), 'Log In')]")\
            .click()
        self.login()


    def login(self):

        try:
            if self.twoAuth:
                """ User needs two factor auth """
                # Enter username
                self.driver.find_element_by_xpath("//input[@name=\"callback_0\"]")\
                    .send_keys(self.username)
                self.driver.find_element_by_xpath('//input[@type="submit"]')\
                    .click()
                # Enter password
                self.driver.find_element_by_xpath("//input[@name=\"callback_1\"]")\
                    .send_keys(self.password)
                self.driver.find_element_by_xpath('//input[@type="submit"]')\
                    .click()
                message = "You are using Two-Factor Authentication.\nI need some help, could you finish loggin us in?\nOnce logged in, enter 'y'."
                self.helpMeHuman(message)
                
            else:
                # Enter username
                self.driver.find_element_by_xpath("//input[@name=\"callback_0\"]")\
                    .send_keys(self.username)
                self.driver.find_element_by_xpath('//input[@type="submit"]')\
                    .click()
                # Enter password
                self.driver.find_element_by_xpath("//input[@name=\"callback_1\"]")\
                    .send_keys(self.password)
                self.driver.find_element_by_xpath('//input[@type="submit"]')\
                    .click()
        
        except Exception as error:
            print("==========================")
            print(error)
            print("Retry logging in...")
            print("==========================")
            self.login()
        
        # Select Site preference
        select_map = {
            'JP': '1',
            'UK': '8',
            'HK': '5',
            'AU': '7',
            'KR': '10'
            }
        idx = select_map[self.site]
        script = 'arguments[0].selectedIndex = {}; arguments[0].onchange();'.format(idx)
        sites = self.driver.find_element_by_xpath('//select[@id="SelectedSiteID"]')
        self.driver.execute_script(script, sites)
        
        # Confirm you logged in
        print("==========================")
        print("Logged in as: ", self.username)
        print("==========================")

        sleep(3)

    """ Navigate to Product Page """
    def navProducts(self):
        
        self.driver.get("https://staging-eu01-lululemon.demandware.net/on/demandware.store/Sites-Site/default/ViewProductList_52-List?SelectedMenuItem=prod-cat&CurrentMenuItemId=prod-cat&CatalogItemType=Product")
        
        self.driver.find_element_by_link_text('By ID').click()
        
        print("==========================")
        print("Product Page")
        print("==========================")
    
            
    """ Search for Products in Products Tool """
    def searchProducts(self, products):
        # Return if no products
        if len(products) == 0:
            return 

        # The search input textarea
        searchInput = self.driver.find_element_by_xpath("//textarea[@name=\"WFSimpleSearch_IDList\"]")
        # Transform array to string with JS and update searchInput
        self.driver.execute_script("arguments[0].value = {}.toString()".format(products), searchInput) 
        
        print("==========================")
        print("Searching: ", products)
        print("==========================")

        SimSearch = self.driver.find_element_by_xpath('//*[@id="IDListDiv"]/form')
        try:
            self.driver.find_element_by_xpath('//button[@name=\"findIDList\"]').click()
        except Exception as error:
            try: 
                SimSearch.submit()
            except:
                self.helpMeHuman("Help Me Click Enter")

    """ Get Primary and SubCategories Assignment from CSV to pass to #setCategories """
    def getCategories(self):
        
        pCats = {}
        sCats = {}

        with open (self.category_csv, newline = '', encoding='UTF-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader: 
                try:
                    """ PERSONAL MAC """
                    master = row['master']
                except:
                    """ OFFICE WINDOWS """
                    master = row['\ufeffmaster']
                
                primary = row['primaryCategory']
                secondary = [cat.strip() for cat in row['subCategories'].split(',')]
                
                # not primary for this product
                if len(primary) < 1:
                    pass
                else:
                    # add to primary list
                    if primary in pCats.keys():
                        pCats[primary].add(master)
                    else: 
                        # remove duplicate masters 
                        pCats[primary] = set([master])
                
                for sec in secondary:
                    if len(sec) < 1:
                        continue
                    if sec in sCats.keys():
                        sCats[sec].add(master)
                    else:
                        sCats[sec] = set([master])
                    
        print("==========================")
        print("Primary Categories to merchandise: ",pCats)
        print("==========================")
        print("Sub Categories to merchandise: ",sCats)
        print("==========================")
        
        return [pCats, sCats]

    """ Assign Primary and Subcategories to Products """
    def setCategories(self, primary, secondary):
            
        while primary or secondary: 

            try: 
                category = next(iter(primary))
                isPrimary = True
                job = "Primary Categorized"
            except:
                category = next(iter(secondary))
                isPrimary = False
                job = "Secondary Categorized"
                
            try:
                products = list(primary[category])
            except: 
                products = list(secondary[category])
                
            print("==========================")
            print("Merchandising: ", category)
            print("==========================")

            self.searchProducts(products)
            
            self.editAll_ProductTool()
            
            print("==========================")
            print("Found: ", products)
            print("==========================")
            
            self.driver.find_element_by_xpath("//input[@value='AssignProductToCatalogCategory']").click()
            
            try:
                self.driver.find_element_by_xpath('//button[@name=\"selectAction\"]').click()
            except:
                script = """document.querySelector("button[name='selectAction']").click()"""
                self.driver.execute_script(script)
            
            try:
                self.driver.find_element_by_xpath('//*[@id="ext-gen77"]').click()
            except:
                script = """"document.querySelector('.x-btn-text.listview_disabled').click()"""
                self.driver.execute_script(script)                  
                    
            try:
                search = self.driver.find_element_by_xpath("//input[@name=\"ext-comp-1009\"]").send_keys(category)
            except:
                sleep(2)
                search = self.driver.find_element_by_xpath("//input[@name=\"ext-comp-1009\"]").send_keys(category)
            
            print("==========================")
            print("Categorizing: ", products)
            print("==========================")
            
            try:
                self.driver.find_element(By.ID, "ext-comp-1009").send_keys(Keys.ENTER)
                self.driver.find_element(By.CSS_SELECTOR, ".x-grid3-row-checker").click()
            except:
                try:
                    search = self.driver.find_element_by_xpath('/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/form/table[1]/tbody/tr[2]/td[2]/div/div/div/div/div[2]/div/div[1]/div/table/tbody/tr/td[2]/div/span/img[1]')
                    search.click()
                    self.driver.find_element(By.CSS_SELECTOR, ".x-grid3-row-checker").click()
                except:
                    message = "Category ID not found. Search ID and select the checkbox then enter 'y'."
                    self.helpMeHuman(message)
                        
            try:
                self.driver.find_element(By.NAME, "selectAction").click()
            except:
                try:
                    selectAction = """document._getElementsByXPath('//button[@name="selectAction"]')[0].click();
                    """
                    self.driver.execute_script(selectAction)
                except:
                    message = "This is embarrassing. Press 'Next' for me please! Then enter 'y'."
                    self.helpMeHuman(message)
            
            if isPrimary:
                dropdown = self.driver.find_element_by_xpath('//select[@name="PrimaryCategoryUUID"]')
            
                options = dropdown.find_element_by_xpath("//option[contains(text(), 'lululemon')]")\
                    .click()
            
            try:
                self.driver.find_element_by_xpath('//button[@name="assignProductsAndReturn"]')\
                .click()
            except:
                try:
                    sleep(2)
                    self.driver.find_element_by_xpath('//button[@name="assignProductsAndReturn"]')\
                    .click()
                except:
                    assignAction = """document._getElementsByXPath('//button[@name="assignProductsAndReturn"]')[0].click();"""
                    self.driver.execute_script(assignAction)
                
                
            
            print("==========================")    
            print("%s: %s > %s" % (job, products, category))
            print("==========================")

            try:
                primary.pop(category)
            except:
                secondary.pop(category)

    def helpMeHuman(self, message):
        print("\nHey %s user! I'm in a pickle here...\nCan you help me??" % (self.site))
        print("Message: " + message)
        stuck = True
        
        while stuck:
            user = input("Are we ready? > ")
            if user != 'y':
                continue
            else:
                stuck = False
                break            
        
        return
    
    def editAll_ProductTool(self):
        try:
            self.driver.find_element_by_xpath('//button[@name=\"EditAll\"]')\
                .click()
        except:
            edit_all = """
                button = document._getElementsByXPath('//button[@name=\"EditAll\"]')
                button[0].click()
            """
            self.driver.execute_script(edit_all)
        
    def navigate_pricebook(self, price_book):
        url = 'https://staging-eu01-lululemon.demandware.net/on/demandware.store/Sites-Site/default/ViewPriceBook_52-Edit?PriceBookID='
        url = url + price_book
        self.driver.get(url)
        self.driver.find_element(By.LINK_TEXT, "Price Definitions").click() 
        self.driver.find_element(By.CSS_SELECTOR, "td:nth-child(3) > .perm_not_disabled").click()
        print(f"Entered {price_book} Price Book Page")
    
    def delete_price_wtih_wild_card(self, skuDict):
        search = self.driver.find_element_by_xpath("//input[@name=\"SearchTerm\"]")
        search.clear()
        keys = [*skuDict]
        total = len(keys)
        count = 0
        
        while keys: 
            key = keys[0]
            skus = skuDict[key]            
            search = self.driver.find_element_by_xpath("//input[@name=\"SearchTerm\"]")
            search.clear()            
            searchTerm = str(key) + '*'
            search.send_keys(searchTerm)
            self.driver.find_element_by_xpath('//button[@name=\"simpleSearch\"]').click()
            
            script = """
                let a = {};
                const i = document._getElementsByXPath('//input[@name="sku"]')
                let found = true;
                let clicked = 0
                
                if (i.length === 0) {{ 
                        found = false;
                }} else {{
                    const ar = Array.from(i);
            
                    ar.forEach((el)=> {{
                        if (a.include(el.defaultValue)) {{
                                el.click();
                                clicked += 1;
                        }}
                    }})
                    
                    if (clicked === 0) {{ found = false; }}
                }}
                return found;
            """.format(skus)
            
            event = self.driver.execute_script(script)
            
            if (event):
                deleteButton = self.driver.find_element_by_xpath('//*[@id="deleteButton"]')
                self.driver.execute_script("arguments[0].click();", deleteButton)
                confirmDelete = self.driver.find_element_by_xpath('//button[@name=\"deletePrices\"]')   
                self.driver.execute_script("arguments[0].click();", confirmDelete)
                print("Deleted: ", skus)
            else: 
                print("Sku not found", skus)
            done = keys.pop(0)
            count += 1
            
            print("{} / {}".format(count, total))
        
    def delete_price_book(self, price_book):
        skus = getSkus()
        skuSorted = mergeSort(skus)
        skuDict = wildCardDict(skuSorted)
        self.navigate_pricebook(price_book)
        self.delete_price_wtih_wild_card(skuDict)