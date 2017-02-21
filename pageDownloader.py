import urllib2
from bs4 import BeautifulSoup
import json
import requests
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from PIL import Image
import urllib


register_openers()
baseServer = 'http://localhost:3000/'



def findTag( tagName ):
  urlstring = baseServer + 'tags/search/' + urllib2.quote(tagName, safe='')
  url = urllib2.Request(urlstring)
  response = urllib2.urlopen(url).read()
  data = json.loads(response);
  if len(data) > 0:
    return data[0]['id']
  else:
    return -1

def addTag( tagName ):
  payload = {'displayName': tagName}
  headers = {'content-type': 'application/json'}
  request = urllib2.Request(baseServer + 'tags/', data = json.dumps(payload), headers = headers)
  response = urllib2.urlopen(request).read()
  data = json.loads(response);
  return data['id']


def addImage( imageURL ):
  f = open('00000001.jpg','wb')
  f.write(urllib2.urlopen(imageURL).read())
  f.close()
  with Image.open('00000001.jpg') as im:
    width, height = im.size
    ratio = width/height
    
    data = [{'width':640, 'height':640/ratio},{'width':1280, 'height':1280/ratio}]
    params = {'file': open("00000001.jpg", "rb"), 'sizes': json.dumps(data) }
    datagen, headers = multipart_encode(params)
    r = urllib2.Request(baseServer + 'images/upload', datagen, headers)
    response = urllib2.urlopen(r).read()
    return json.loads(response)['id']


def addProduct( displayName, productCode, itemCode, imageURL, sourcePage, Tags ):
  print '-------'
  print 'DisplayName: ' + displayName
  print 'productCode: ' + productCode
  print 'itemCode: ' + itemCode
  print 'imageURL: ' + imageURL
  print 'sourcePage: ' + sourcePage
  imageId = addImage(imageURL)
  tagsToAdd = []

  for tag in Tags:
    foundTag = findTag(tag)
    if foundTag < 0:
      foundTag = addTag(tag)

    alreadyInserted = False
    for tagAlreadyAdded in tagsToAdd:
      if tagAlreadyAdded['id'] == foundTag:
        alreadyInserted = True
    if not alreadyInserted:
      tagId = {}
      tagId['id'] = foundTag
      tagsToAdd.append(tagId)
  print tagsToAdd;  
  url = baseServer + 'products/'
  data = {'displayName' : displayName,'itemCode':itemCode, 'sourceURL':sourcePage , 'productCode'  : productCode, 'BrandId': 1, 'ImageId': imageId, 'Tags': tagsToAdd }
  
  headers = {'content-type': 'application/json'}
  request = urllib2.Request(url, data = json.dumps(data), headers = headers)

  response = urllib2.urlopen(request).read()
  print response
  print '---------------'


start = 120
while True:
  req = urllib2.Request('http://www.adidas.com/us/search?sz=120&start='+(str(start))+'&fdid=STORIES&format=ajax', headers={'User-Agent':"Magic Browser"})
  start = start + 120;
  response = urllib2.urlopen(req)
  content = response.read()
  structured_page = BeautifulSoup(content)

  #find all objects
  items = structured_page.find_all("div", class_="innercard")
  print 'total products: ' + str(len(items))
  for item in items:

    productName = item.find("div", class_="plp-image-bg").find('a').get('data-productname');

    hasMultile = item.find("div", class_="jcarousel");
    print 'HAS MULTIPLE'
    print hasMultile
    print '========'
    if hasMultile is None:
      #this item doesn't have permutation, fetch the data from different tags.
      img =  item.find('img')
      productImage = img.get('data-original').replace('sw=230', 'sw=2000');
      deepLink = item.find('a', class_="plp-image-bg-link").get('href')
      title = img.get('title')
      productCode = deepLink.split("/")[4];
      rowTags = img.get('alt');
      title = img.get('title');
      colorId = item.find('a', class_="plp-image-bg-link").get('data-track');
      tags = rowTags[rowTags.find(title)+len(title):rowTags.find(colorId)].split(" / ")
      processedtags = list()
      for tag in tags:
        processedtags.append(tag.strip())
      #PRODUCT PAGE REQUEST
      deepRequest = urllib2.Request(deepLink, headers={'User-Agent':"Magic Browser"})
      deepResponse = urllib2.urlopen(deepRequest)
      deepContent = deepResponse.read()
      deep_structured_page = BeautifulSoup(deepContent)
      breadcrumb = deep_structured_page.find("ul", class_='breadcrumb');
      extraTags = breadcrumb.find_all('li')[2:]
      extraTags.pop()
      for extraTag in extraTags:
        processedtags.append(extraTag.get('data-context').capitalize())

      addProduct(productName, productCode, productCode+'-'+colorId,productImage,deepLink,processedtags)
    else:
      print item
      print '-----'
      print item.find('ul')
      print '-----'
      possibleProducts = item.find('ul').find_all('li');
      print 'possible products'
      print possibleProducts
      for permutation in possibleProducts:
        img =  permutation.find('img')
        print 'img'
        print img
        productImage = img.get('data-original').replace('sw=60', 'sw=2000');
        deepLink = img.get('data-url')
        productCode = deepLink.split("/")[4];
        rowTags = img.get('alt');
        title = img.get('title')
        colorId = img.get('data-colorid')
        tags = rowTags[rowTags.find(title)+len(title):rowTags.find(colorId)].split(" / ")
        processedtags = list()
        for tag in tags:
          processedtags.append(tag.strip())
        #PRODUCT PAGE REQUEST
        deepRequest = urllib2.Request(deepLink, headers={'User-Agent':"Magic Browser"})
        deepResponse = urllib2.urlopen(deepRequest)
        deepContent = deepResponse.read()
        deep_structured_page = BeautifulSoup(deepContent)
        breadcrumb = deep_structured_page.find("ul", class_='breadcrumb');
        extraTags = breadcrumb.find_all('li')[2:]
        extraTags.pop()
        for extraTag in extraTags:
          processedtags.append(extraTag.get('data-context').capitalize())

        addProduct(productName, productCode, productCode+'-'+colorId,productImage,deepLink,processedtags)


