# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 12:42:31 2021

@author: hlau2
"""



import csv

def getSkus():

    skus = []

    with open ('./csv/delete_sale_skus.csv', newline = '', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader: 
            sku = int(row['skus'].strip())
            skus.append(sku)

    return skus

    
def mergeSort(arr):
    if len(arr) < 2:
        return arr
    mid = len(arr) // 2

    left = arr[:mid]
    right = arr[mid:]

    leftSort = mergeSort(left)
    rightSort = mergeSort(right)
    
    result = merge(leftSort, rightSort)
    
    return result
    

def merge(arr1, arr2):
    result = []
    while len(arr1) > 0 and len(arr2) > 0:
        if arr1[0] < arr2[0]:
            nextItem = arr1.pop(0)
        else:
            nextItem = arr2.pop(0)
        result.append(nextItem)
    result = result + arr1 + arr2
    return result


def wildCardDict(arr):
    mapping = {}
    
    for sku in arr:
        k = sku // 10
        if k in mapping.keys():
            mapping[k].append(sku)
        else:
            mapping[k] = [sku]
    return mapping
 