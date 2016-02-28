from urllib.parse import urlparse
import time
import random
from pathlib import Path
import zipfile
import requests
from selenium import webdriver


HERE = Path(__file__).parent

driver = webdriver.Firefox()


def main():
    scraper = Scraper(
        name='少女新娘物语 Vol 2',
        url='http://www.jmydm.com/comicdir/201049/')
    scraper.download()
    scraper.archive()
    driver.quit()


class Scraper:
    def __init__(self, name, url, cache_dir=None):
        self.name = name
        self.url = url
        cache_dir = HERE / 'cache'
        self.output_dir = cache_dir / name
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        self.user_agent = driver.execute_script('return window.navigator.userAgent')

    def download(self):
        driver.get(self.url)
        # First, open the page navigation element.
        page_button = driver.find_elements_by_css_selector('#iPageNo')[0]
        page_button.click()

        self.download_largest_image(1)

        for page in self.get_pages():
            print(page)
            if self.page_downloaded(page):
                continue
            driver.execute_script('csel(%d)' % page)
            self.download_largest_image(page)
            self.sleep()

    def archive(self):
        output_path = Path('.') / ('%s.zip' % self.name)
        with zipfile.ZipFile(str(output_path), 'w') as zf:
            for file_ in self.output_dir.glob('*.jpg'):
                print(file_)
                zf.write(str(file_))
                # zf.writestr(file_.name, file_.read_bytes())

    def sleep(self):
        time.sleep(random.randint(1, 5))

    def get_pages(self):
        anchors = driver.find_elements_by_css_selector('.cPageChangeHtm a')
        page_numbers = [a.text for a in anchors[1:]]
        for page_number in page_numbers:
            yield int(page_number)

    def page_downloaded(self, page_number):
        return list(self.output_dir.glob('%d.*' % page_number))

    def download_largest_image(self, page_number):
        if self.page_downloaded(page_number):
            return
        image_url = self.get_largest_image_url()
        # print(image_url)
        headers = {
            'user-agent': self.user_agent,
            'host': urlparse(image_url).netloc,
            'referer': driver.current_url,
            'accept': 'image/png,image/*;q=0.8,*/*;q=0.5',
            'accept-language': 'Accept-Language: en-US,en;q=0.5',
            'connection': 'keep-alive',
        }
        ext = image_url.rsplit('.', 1)[1].lower()
        output_path = self.output_dir / ('%d.%s' % (page_number, ext))
        print('Downloading page %d to %s' % (page_number, output_path))
        response = requests.get(image_url, headers=headers)
        with output_path.open('wb') as fp:
            fp.write(response.content)

    def get_largest_image_url(self):
        return driver.execute_script(JAVASCRIPT)


JAVASCRIPT = """
var images = document.querySelectorAll('img');
var maxArea = 0;
var biggestImage = null;

for (var i=0; i < images.length; i++) {
    var img = images[i];
    if (img.style.display === 'none') {
        continue;
    }
    var area = img.naturalWidth * img.naturalHeight;
    if (biggestImage === null || area > maxArea) {
        maxArea = area;
        biggestImage = img;
    }
}
console.log(area, biggestImage)
return biggestImage.src
"""


if __name__ == '__main__':
    main()
