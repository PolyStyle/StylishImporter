import urllib2
from bs4 import BeautifulSoup


def addProduct( displayName, productCode, itemCode, imageURL, sourcePage, Tags ):
  print '-------'
  print 'DisplayName: ' + displayName
  print 'productCode: ' + productCode
  print 'itemCode: ' + itemCode
  print 'imageURL: ' + imageURL
  print 'sourcePage: ' + sourcePage
  print 'Tags: ' + (''.join(Tags))
  print '-------'
  return

req = urllib2.Request('http://www.adidas.com/us/search?sz=120&start=0&fdid=STORIES&format=ajax', headers={'User-Agent':"Magic Browser"})
response = urllib2.urlopen(req)
content = response.read()
structured_page = BeautifulSoup(content)

#find all objects
items = structured_page.find_all("div", class_="innercard")
print 'total products: ' + str(len(items))
for item in items:

  productName = item.find("div", class_="plp-image-bg").find('a').get('data-productname');

  if not hasattr(item.find('ul'), 'fina_all'):
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
    possibleProducts = item.find('ul').find_all('li');

    for permutation in possibleProducts:
      img =  permutation.find('img')
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


