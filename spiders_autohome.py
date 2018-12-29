# coding:utf-8

import requests
from bs4 import BeautifulSoup
import time, re, os, sys, logging

if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

dir_path = '../autohome'
start_brand_id = 1 # default=1
start_series_id = 1 # default=1
start_EOL_status = False # default=False
start_page = 1 # default=1

stop_brand_id = 99999


''' log '''
# 第一步，创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Log等级总开关
# 第二步，创建一个handler，用于写入日志文件
rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
logfile = os.path.join(os.getcwd(), rq+'.log')
fh = logging.FileHandler(logfile, mode='w')
fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
# 第三步，定义handler的输出格式
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
# 第四步，将logger添加到handler里面
logger.addHandler(fh)
# terminor
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # 输出到console的log等级的开关
ch.setFormatter(formatter)
logger.addHandler(ch)


def mkdir(path):
    path = path.replace('・', '·')
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def save_imgurl(url='https://car.autohome.com.cn/photo/series/7549/1/694188.html',save_path='.\\'):
    assert (len(url)), 'url=%s'%url
    assert (os.path.isdir(save_path)), 'url=%s'%url

    res = requests.get(url)
    res.encoding = 'gb2312'
    html = res.text
    soup = BeautifulSoup(html, 'html.parser')

    # get img url
    img_src = soup.find('div', class_='pic')
    if img_src == None:
        return
    img_src = 'https:' + img_src.find('img')['src']

    # get vehicle color
    title_list = soup.find_all('h2', class_='section-title')
    color_name = ''
    for title in title_list:
        if title.next != '外观颜色: ': continue
        color_title = title.nextSibling.find('a', class_='red')
        if color_title != None:
            color_name = color_title['title']

    if color_name == '':
        save_path = os.path.join(save_path, 'none')
    else:
        save_path = os.path.join(save_path, color_name.strip())
    save_path = mkdir(save_path)



    # save img
    data = requests.get(img_src, stream=True).content
    with open(os.path.join(save_path, img_src.split('/')[-1]), 'wb') as fp:
        fp.write(data)
    logger.info('save: %s'%save_path)
    # time.sleep(1)


def series2imgurl(url='https://car.autohome.com.cn/pic/series/526-1.html#pvareaid=2042222', root_path='.\\'):
    assert (len(url)), 'url=%s'%url
    assert (len(root_path)), 'url=%s'%url

    res = requests.get(url)
    res.encoding = 'gb2312'
    html = res.text
    soup = BeautifulSoup(html, 'html.parser')
    uibox = soup.find('div', class_='uibox-con carpic-list03')
    if uibox == None:
        uibox = soup.find('div', class_='uibox-con carpic-list03 border-b-solid')
        if uibox == None:
            logger.info('def series2imgurl, uibox==None, url= %s'%url)
            return False

    ## mkdir
    breadnav_list = soup.find('div', class_='breadnav').find_all('a')[2:]
    assert(len(breadnav_list)), 'url=%s'%url
    for breadnav in breadnav_list:
        dirname = breadnav.string
        root_path = os.path.join(root_path, dirname.strip())
    root_path = mkdir(root_path)


    div_list = uibox.find_all('div')
    if len(div_list) == 0:
        return False
    for div in div_list:
        a = div.find('a')
        series_name = a.string
        if series_name == None or series_name == '':
            continue
        series_path = os.path.join(root_path, series_name.strip())
        series_path = mkdir(series_path)

        series_url = a['href']
        series_url = 'https://car.autohome.com.cn' + series_url

        save_imgurl(series_url, series_path)

    return True


def brand2series(url='https://car.autohome.com.cn/pic/brand-15.html', root_path='.\\'):
    global start_series_id, start_EOL_status, start_page
    assert(len(url)), 'url=%s'%url
    assert(len(root_path)), 'url=%s'%url
    res = requests.get(url)
    res.encoding = 'gb2312'
    html = res.text
    soup = BeautifulSoup(html, 'html.parser')
    uibox_list = soup.find_all('div', class_='uibox-con carpic-list02')
    series_count = 0
    for uibox in uibox_list:
        div_list = uibox.find_all('div')
        for div in div_list:
            series_count += 1
            if series_count < start_series_id:
                continue
            start_series_id = 0

            a = div.find('a')
            series_url = a['href']

            if not start_EOL_status:
                assert('.html#pvareaid=2042214' in series_url), 'url=%s'%url
                pagecont = 0
                while True:
                    pagecont += 1
                    if pagecont < start_page:
                        continue
                    start_page=0
                    series_url_run = series_url.replace('.html#pvareaid=2042214','-1-p%d.html'%pagecont)
                    series_url_run = 'https://car.autohome.com.cn' + series_url_run
                    logger.info('series_count=%d, EOL=False, page=%d: %s' % (series_count, pagecont, series_url_run))
                    if not series2imgurl(series_url_run,root_path):
                        break

            start_EOL_status = False

            assert('pic/series' in series_url), 'url=%s'%url
            pagecont = 0
            series_url_EOL = series_url.replace('pic/series', 'pic/series-t')
            while True:
                pagecont += 1
                if pagecont < start_page:
                    continue
                start_page = 0
                series_url_EOL_run = series_url_EOL.replace('.html#pvareaid=2042214','-1-p%d.html'%pagecont)
                series_url_EOL_run = 'https://car.autohome.com.cn' + series_url_EOL_run
                logger.info('series_count=%d, EOL=True, page=%d: %s' % (series_count, pagecont, series_url_EOL_run))
                if not series2imgurl(series_url_EOL_run,root_path):
                    break


def main():
    res = requests.get('https://car.autohome.com.cn/AsLeftMenu/As_LeftListNew.ashx?typeId=2%20&brandId=0%20&fctId=0%20&seriesId=0')
    res.encoding = 'gb2312'
    html = res.text
    soup = BeautifulSoup(html, 'html.parser')
    li_brand_list = soup.find_all('li')

    brand_count = 0
    for li_brand in li_brand_list:
        brand_count += 1
        if brand_count < start_brand_id:
            continue
        if brand_count >= stop_brand_id:
            break

        a_brand = li_brand.find('a')
        brand_name = a_brand.next.next
        href = a_brand['href']
        href_url = 'https://car.autohome.com.cn' + href

        logger.info('brand_count=%d: %s'%(brand_count, href_url))
        brand2series(url=href_url, root_path=dir_path)

    print('\ndone.\n')


if __name__ == '__main__':
    main()


    # brand2series()
    # series2imgurl()
    # save_imgurl()
