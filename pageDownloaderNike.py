import urllib2
from bs4 import BeautifulSoup
import json
import requests
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from PIL import Image
import urllib
from joblib import Parallel, delayed
import multiprocessing


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
  f = open('00000002.jpg','wb')
  f.write(urllib2.urlopen(imageURL).read())
  f.close()
  with Image.open('00000002.jpg') as im:
    width, height = im.size
    ratio = width/height

    data = [{'width':640, 'height':640/ratio},{'width':1280, 'height':1280/ratio}]
    params = {'file': open("00000002.jpg", "rb"), 'sizes': json.dumps(data) }
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
  url = baseServer + 'products/'
  data = {'displayName' : displayName,'itemCode':itemCode, 'sourceURL':sourcePage , 'productCode'  : productCode, 'BrandId': 8, 'ImageId': imageId, 'Tags': tagsToAdd }

  headers = {'content-type': 'application/json'}
  request = urllib2.Request(url, data = json.dumps(data), headers = headers)

  response = urllib2.urlopen(request).read()
  print '---------------'


def crawl():
  start = 600
  while True:
    req = urllib2.Request('http://www.adidas.com/us/search?sz=120&start='+(str(start))+'&fdid=STORIES&format=ajax', headers={'User-Agent':"Magic Browser"})

    start = start + 120;

    response = urllib2.urlopen(req)
    content = response.read()
    structured_page = BeautifulSoup(content)

    #find all objects
    items = structured_page.find_all("div", class_="innercard")
    print 'total products: ' + str(len(items))
    counter = 0;
    for item in items:
      print str(start - 120 + counter)
      counter = counter + 1
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
        print '-----'
        possibleProducts = item.find('ul').find_all('li');
        print 'possible products'
        print possibleProducts
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


cookie = 'AnalysisUserId=2.22.23.117.15094148766969239; geoloc=cc=SE,rc=AB,tp=vhigh,tz=GMT+1,la=59.33,lo=18.05,bw=5000; guidU=5aec6586-4555-40d3-d875-d434b30c2b79; neo.swimlane=74; dreams_sample=52; AMCVS_F0935E09512D2C270A490D4D%40AdobeOrg=1; NIKE_COMMERCE_CCR=1487669697770; CONSUMERCHOICE_SESSION=t; CONSUMERCHOICE=us/en_us; NIKE_COMMERCE_COUNTRY=US; NIKE_COMMERCE_LANG_LOCALE=en_US; AKNIKE=3sd8LBeVlk0MmKaVE2sohPY4qc1JhuGhRJapZ8o7B3YIgtFvkPVXe6g; RES_TRACKINGID=23238830000796678; fbm_84697719333=base_domain=.nike.com; isGeolocCommerce=true; nike_locale=us/en_us; guidA=73ff140239710000ee23ac585b020000a4280000; guidS=8f016588-e057-4517-a3f9-b07e9b182c19; AMCV_F0935E09512D2C270A490D4D%40AdobeOrg=2121618341%7CMCIDTS%7C17219%7CMCMID%7C58539422994532574832321745659623283384%7CMCAAMLH-1488274493%7C6%7CMCAAMB-1488289574%7CNRX38WO0n5BH8Th-nqAG_A%7CMCOPTOUT-1487691974s%7CNONE%7CMCAID%7CNONE; utag_main=_st:1487689731730$ses_id:1487684894868%3Bexp-session; guidSTimestamp=1487684772925|1487687932655; DAPROPS="sdevicePixelRatio:1|sdeviceAspectRatio:16/9|bcookieSupport:1"; tfc-l=%7B%22a%22%3A%7B%22v%22%3A%2275de0547-a87c-4df3-909a-0b04d9da048f%22%2C%22e%22%3A1487774333%7D%2C%22u%22%3A%7B%22v%22%3A%22V5%7Cunk_7186c4c0-5825-4702-9224-c3b7f906938f%7C1550575613%22%2C%22e%22%3A1550575618%7D%2C%22s%22%3A%7B%22v%22%3A%22%22%2C%22e%22%3A1550575518%7D%7D; tfc-s=%7B%22v%22%3A%22tfc-fitrec-product%3D14%22%7D; ResonanceSegment=1; mp_nike_mixpanel=%7B%22distinct_id%22%3A%20%2215a60062615333-09c0342e1a855-1d3b6853-384000-15a6006261695d%22%7D; stc111680=env:1487684774%7C20170324134614%7C20170221150854%7C6%7C1015907:20180221143854|uid:1487669707475.271700424.49903536.111680.1766869948:20180221143854|srchist:1015907%3A1487684774%3A20170324134614:20180221143854|tsa:1487684774613.1059931536.1314735.932295263099117.1:20170221150854; s_pers=%20s_dfa%3Dnikecomprod%7C1487689731926%3B%20c5%3Dnikecom%253Epdp%253ENIKE%2520AIR%2520ZOOM%2520PEGASUS%252033%7C1487689735281%3B%20c6%3Dpdp%253Ainstant%2520personalization%7C1487689735285%3B%20c58%3Dno%2520value%7C1487689735299%3B%20ppm%3D%257B%2522name%2522%253A%2522direct%2520entry%2522%252C%2522detail%2522%253A%2522direct%2520entry%2522%252C%2522st%2522%253Anull%257D%7C1519223935306%3B; s_sess=%20s_sq%3D%3B%20tp%3D5489%3B%20s_ppv%3Dnikecom%25253Epdp%25253ENIKE%252520AIR%252520ZOOM%252520PEGASUS%25252033%252C12%252C12%252C664%3B%20c51%3Dhorizontal%3B%20prevList2%3D%3B%20s_cc%3Dtrue%3B; fbsr_84697719333=cdSkvvlUkDkEbIIcEC7GzXqSk3v-M65o4TeqcqybZ1E.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJBUUIzNU9YYm52NnUtOGFTRzcyS2t3dnF0YzVFbGZ4X1pVOVdDajZnTXdsX0xySWhJR0NMTXJ0ZWl2Ykh6LTFfa21MMlNBUFJjeG5KVjRNN0F0Q05JcTFRWEozYWUyYzZVVy1fZVFyVUVGNVJFZFpFODZCZ1FvdW55NWZhSHJFdUhNZl9tWkJLcWpPM0FPQUtXa2R0M3hodUFTN0dzcmJXVklhTll5SklfUmFLWEZTZ0dlRjZlaE1oOERPTktCd0szYTBmLWNaMlFaVzJNakVKamFxR0FUaGktVmR0SmwzQ0lGT0QzaTBaS2JvSDRLeXg4OTg1eVZuS0pqMktuaUoxRTE4dUNHOXlwYU91cGs1UW94ZTR5dHZhd0t6S25uTnlNUXpyWXJUZnU3S3Z0djJ6WXM5V1RFTU5mWERHUUctc2x1RWtoVDFvMTFtOGtDcWN4cnFpekNKaFU1b3BodUlnR2tDS20tN3hQM0E1ZWE4NFVhTGVNU3B1SzV1MW9mOVIxN3ciLCJpc3N1ZWRfYXQiOjE0ODc2OTE4MzUsInVzZXJfaWQiOiIxMDAwMDM1NTUxMzIwNjgifQ; RT="dm=nike.com&si=9ecf83b0-db50-47d3-b880-b40e10a4e9c3&ss=1487687930391&sl=0&tt=0&obo=0&sh=&bcn=%2F%2F364bf52e.mpstat.us%2F&ld=1487687933987&r=http%3A%2F%2Fstore.nike.com%2Fus%2Fen_us%2Fpd%2Fair-zoom-pegasus-33-mens-running-shoe%2Fpid-11155764%2Fpgid-11914121&ul=1487692086530'



def processLinks(links):
  print 'totalLinks: ' + str(len(links))
  count = 0
  for link in links:
    print count
    print link
    count = count +1
    req = urllib2.Request(link, headers={'User-Agent':"Magic Browser", 'Cookie': cookie})
    response = urllib2.urlopen(req)
    content = response.read()
    structured_page = BeautifulSoup(content, "lxml")
    f = open('singleProduct', 'wb')
    f.write(str(structured_page))
    if structured_page.find("h1", class_="exp-product-title") is not None:
      productName = structured_page.find("h1", class_="exp-product-title").contents[0]
      productCode = link.split("/")[6];
      itemCode = link.split("/")[7].split("-")[1];
      productImage = structured_page.find_all("img", class_="exp-pdp-hero-image")[0].get('data-src-large').split('?')[0]
      sourcePage = link
      Tags = {'Men','Shoes'}
      #displayName, productCode, itemCode, imageURL, sourcePage, Tags
      addProduct(productName, productCode, itemCode, productImage, sourcePage, Tags)

req = urllib2.Request('http://store.nike.com/us/en_us/pw/mens-nike-shoes/7puZpipZoi3?ipp=800', headers={'User-Agent':"Magic Browser", 'Cookie': cookie})
response = urllib2.urlopen(req)
content = response.read()
structured_page = BeautifulSoup(content, "lxml")
items = structured_page.find_all("div", class_="grid-item")
print 'total products: ' + str(len(items))
counter = 0;
linksToProcess = []
for item in items:
  links = item.find_all("a")
  if len(links) > 1:
    links = links[1:]
  for l in links:
    linksToProcess.append(l.get('href'))

processLinks(linksToProcess[174:])



