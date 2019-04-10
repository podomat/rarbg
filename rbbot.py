#-*- coding: utf-8 -*-

from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import sys
from time import sleep
import os
import requests
import shutil
import logging


class RBTorrentTrawler:
	
	# 생성자
	def __init__(self):
		self.init_log('rarbg')
		self.webdriver_path = '..\chromedriver\chromedriver'
		#self.webdriver_path = 'C:\eData\geckodriver\geckodriver.exe'
		self.id = ''
		self.pw = ''
		self.name = u''
		#self.base_url = 'http://rarbg.is'
		self.base_url = 'http://rarbgprx.org'
		self.url_prefix = self.base_url + '/torrents.php?category=1;4'
		self.human_check_url = self.base_url + '/threat_defence.php?defence=1'
		self.comment_alert = u''
		self.listPageUrlFormat = self.base_url + '/torrents.php?search={0}&category={1}&page={2}'
		self.data_dir = '../rarbg_data/'
		
	
	# 소멸자
	def __del__(self):
		self.driver.close()
		for handler in self.log.handlers:
			handler.close()
			self.log.removeFilter(handler)
		pass
	
	# 로그 초기화
	def init_log(self, log_name):
		self.log = logging.getLogger(log_name)
		self.log.setLevel(logging.INFO)
		formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] %(message)s', '%H:%M:%S')
		
		ch = logging.StreamHandler(sys.stdout)
		ch.setFormatter(formatter)
		#self.log.addHandler(ch)
		
		fh = logging.FileHandler('{0}.log'.format(log_name))
		fh.setFormatter(formatter)
		self.log.addHandler(fh)
		
	
	# 웹 드라이버 초기화
	def init_driver(self):
		options = webdriver.ChromeOptions()
		#options.add_argument('headless')
		#options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
		#prefs = {'profile.managed_default_content_settings.images':2}
		#options.add_experimental_option("prefs", prefs)
		self.driver = webdriver.Chrome(self.webdriver_path, chrome_options=options)
		#self.driver = webdriver.Firefox(executable_path = self.webdriver_path)
		#self.driver.implicitly_wait(5)
		
	
	# 파일 다운로드
	def file_download(self, url, fname):
		self.log.info('Downloading... {0} >> {1}'.format(url, fname))
		while True:
			count = 0
			try:
				r = requests.get(url, stream=True)
				break
			except Exception as e:
				count = count + 1
				self.log.info(e)
				if (count > 3): return -1
				
		if r.status_code == 200:
			with open(fname, 'wb') as f:
				r.raw.decode_content = True
				shutil.copyfileobj(r.raw, f)
		else:
			self.log.info('Download failed, {0}'.format(r.status_code))
			
		return 0

	# magnet link로 url 파일 만들기
	def make_magnet_file(self, magnet_link, fname):
		contents = "[{{000214A0-0000-0000-C000-000000000046}}]\nProp3=19,0\n[InternetShortcut]\nIDList=\nURL={0}\n".format(magnet_link)
		f = open(fname, 'w')
		f.write(contents)
		f.close()
		return 0
	
	# 확장자 추출
	def get_extension(self, url):
		index = url.rfind('.')
		if(index < 0): return None
		return url[index+1:]
		
		
	# 주어진 디렉토리에 파일들을 참고하여 타이틀 목록 추출
	def get_list_of_titles_in_a_directory(self, dir_name):
		titles = []
		files = os.listdir(dir_name)
		count = 0
		for file in files:
			index = file.rfind('_screenshot')
			if (index >= 0) :
				count = count + 1
				titles.append(file[:index])
				self.log.info ('[{0}] {1}'.format(count, file[:index]))
		return titles
		
		
	# 스킵하고 넘길 레이블인지 검사
	def is_skip_title(self, title):
		return False
		
		skip_title_list = [
			'AllOver30',
			'Anilos',
			'Nubiles',
			
			'AbbyWinters',
			'ATKExotics',
			'ATKGalleria',
			'ATKHairy',
			'Bryci',
			'EuroGirlsOnGirls',
			'FacialAbuse',
			'FTVGirls',
			'GirlsOutWest',
			'GrandMams',
			'LadyVoyeurs',
			'MetArt',
			'MomsLickTeens',
			'KatieBanks',
			'OldYoungLesbianLove',
			'PlumperPass',
			'PornMegaLoad',
			'RestrainedElegance',
			'SexArt',
			'WetAndPuffy',
			'WankItNow',
			]
		
		for st in skip_title_list:
			if (st == title[:len(st)]):
				return True
		
		return False


	def download_target(self, item_url, type, dir_name, title):
		self.driver.get(item_url)
		item_html = self.driver.page_source
		item_soup = BeautifulSoup(item_html, 'html.parser')
		
		tlines = item_soup.find('table', {'class':'lista-rounded'}).find('tbody').find_all('tr', recursive=False)[1].find('table').find('tbody').find_all('tr', recursive=False)
		for tline in tlines:
			if(tline.find('td').get_text().strip() == 'Torrent:'):
				tor_src = self.base_url + tline.find('td', {'class':'lista'}).find('a')['href']
				self.log.info('Torrent    : {0}'.format(tor_src))
				magnet_src = tline.find('td', {'class':'lista'}).find_all('a')[1]['href']
				self.log.info('Magnet     : {0}'.format(magnet_src))
			elif(tline.find('td').get_text().strip() == 'Poster:'):
				poster_src = tline.find('td', {'class':'lista'}).find('img')['src']
				#self.log.info('Poster     : {0}'.format(poster_src))
			elif(tline.find('td').get_text().strip() == 'Description:'):
				sshot_url = tline.find('td', {'class':'lista'}).find('a')['href']
				self.log.info('URL        : {0}'.format(sshot_url))
				
		if (type == 'Torrent'):
			#if(self.file_download(tor_src, '{0}/{1}.{2}'.format(dir_name, title, self.get_extension(tor_src))) < 0): return
			#self.log.info('FakeDownloading... {0} >> {1}'.format(tor_src, '{0}/{1}.{2}'.format(dir_name, title, self.get_extension(tor_src))))
			if(self.make_magnet_file(magnet_src, '{0}/{1}.url'.format(dir_name, title)) < 0): return
		else:
			# 스크린샷 페이지 로딩
			self.driver.get(sshot_url)
			sshot_html = self.driver.page_source
			sshot_soup = BeautifulSoup(sshot_html, 'html.parser')
			
			sshot_src = sshot_soup.find('div', {'id':'image_view'}).find('a')['href']
			self.log.info('ScreenShot : {0}'.format(sshot_src))
			
			#self.log.info('dir_name: {0}'.format(dir_name))
			if not os.path.exists(dir_name):
				os.makedirs(dir_name)
				
			#self.file_download(tor_src, '{0}/{1}.{2}'.format(dir_name, title, self.get_extension(tor_src)))
			#self.file_download(poster_src, '{0}/{1}_poster.{2}'.format(dir_name, title, self.get_extension(poster_src)))
			if(self.file_download(sshot_src, '{0}/{1}_screenshot.{2}'.format(dir_name, title, self.get_extension(sshot_src))) < 0): return


	def retrieve_target(self, target_titles, dir_name):
		for title in target_titles:
			r_url = self.base_url + '/torrents.php?search={0}&category=4'.format(title)
			self.driver.get(r_url)
			html = self.driver.page_source
			soup = BeautifulSoup(html, 'html.parser')

			list = soup.find_all('tr', {'class':'lista2'})

			if len(list) > 1:
				self.log.info ('Too many search result... {0}'.format(r_url))
				return

			for item in list:
				title_info = item.find_all('td', {'class':'lista'})[1]
				item_url = self.base_url + title_info.find('a')['href']
				self.download_target(item_url, 'Torrent', dir_name, title)

	
	# 주어진 시작페이지와 날짜에 대한 리스트 페이지를 차례로 열면서 각 포스트에 토렌트 및 스크린샷 파일을 다운로드
	def get_torrent_seeds(self, start_page, target_date, start_post_title, type):
		page = 0
		completed = False
		started = True
		dir_name = self.data_dir + target_date
		
		# CAPCHA 페이지 로딩
		self.driver.get(self.human_check_url)
		for i in range(1, 8):
			self.log.info ('Page loading waiting... {0}'.format(i))
			sleep(1)
		self.driver.find_element_by_xpath('/html/body/div/div/a').click()
		for i in range(1, 15):
			self.log.info ('Input reCAPTCHA waiting... {0}'.format(i))
			sleep(1)

		if (start_page != None): page = start_page - 1
		if (start_post_title != None): started = False
		if (type == 'Torrent' or type == 'Retrieve'): target_titles = self.get_list_of_titles_in_a_directory(dir_name)

		if type == 'Retrieve':
			self.retrieve_target(target_titles, dir_name)
			return
		
		while completed == False:
			page = page + 1
			list_url = self.listPageUrlFormat.format('1080', '4', page)
			
			self.log.info('')
			self.log.info('Page: {0} / {1}'.format(page, list_url))
			
			# 리스트 페이지 로딩
			self.driver.get(list_url)
			html = self.driver.page_source
			soup = BeautifulSoup(html, 'html.parser')
			
			list = soup.find_all('tr', {'class':'lista2'})
			
			for item in list:
				title_info = item.find_all('td', {'class':'lista'})[1]
				title = title_info.get_text().strip()
				item_url = self.base_url + title_info.find('a')['href']
				
				date_info = item.find_all('td', {'class':'lista'})[2]
				date = date_info.get_text().split()[0]
				time = date_info.get_text().split()[1]
				
				
				if (date > target_date): 
					self.log.info('')
					self.log.info('[SKIP] ' + title + ' / ' + item_url + ' / ' + date)
					continue
				if (date < target_date): 
					self.log.info('')
					self.log.info('[END] ' + title + ' / ' + item_url + ' / ' + date)
					completed = True
					break
					
				if (started == False):
					if (start_post_title == title):
						started = True
					else:
						self.log.info('')
						self.log.info('[NY_STARTED] ' + title + ' / ' + item_url + ' / ' + date)
						continue
						
				if (type == 'Torrent'): 
					if (title not in target_titles):
						self.log.info('')
						self.log.info('[NOT_TARGET] ' + title + ' / ' + item_url + ' / ' + date)
						continue
						
				if (self.is_skip_title(title) == True):
					self.log.info('')
					self.log.info('[SKIP_TARGET] ' + title + ' / ' + item_url + ' / ' + date)
					continue
						
				self.log.info('')
				self.log.info('[TARGET] ' + title + ' / ' + item_url + ' / ' + date + ' ' + time)
				
				# 아이템 페이지 로딩
				self.download_target(item_url, type, dir_name, title)
				'''
				self.driver.get(item_url)
				item_html = self.driver.page_source
				item_soup = BeautifulSoup(item_html, 'html.parser')
				
				
				tlines = item_soup.find('table', {'class':'lista-rounded'}).find('tbody').find_all('tr', recursive=False)[1].find('table').find('tbody').find_all('tr', recursive=False)
				for tline in tlines:
					if(tline.find('td').get_text().strip() == 'Torrent:'):
						tor_src = self.base_url + tline.find('td', {'class':'lista'}).find('a')['href']
						self.log.info('Torrent    : {0}'.format(tor_src))
						magnet_src = tline.find('td', {'class':'lista'}).find_all('a')[1]['href']
						self.log.info('Magnet     : {0}'.format(magnet_src))
					elif(tline.find('td').get_text().strip() == 'Poster:'):
						poster_src = tline.find('td', {'class':'lista'}).find('img')['src']
						#self.log.info('Poster     : {0}'.format(poster_src))
					elif(tline.find('td').get_text().strip() == 'Description:'):
						sshot_url = tline.find('td', {'class':'lista'}).find('a')['href']
						self.log.info('URL        : {0}'.format(sshot_url))
						
				if (type == 'Torrent'):
					#if(self.file_download(tor_src, '{0}/{1}.{2}'.format(dir_name, title, self.get_extension(tor_src))) < 0): return
					#self.log.info('FakeDownloading... {0} >> {1}'.format(tor_src, '{0}/{1}.{2}'.format(dir_name, title, self.get_extension(tor_src))))
					if(self.make_magnet_file(magnet_src, '{0}/{1}.url'.format(dir_name, title)) < 0): return
				else:
					# 스크린샷 페이지 로딩
					self.driver.get(sshot_url)
					sshot_html = self.driver.page_source
					sshot_soup = BeautifulSoup(sshot_html, 'html.parser')
					
					sshot_src = sshot_soup.find('div', {'id':'image_view'}).find('a')['href']
					self.log.info('ScreenShot : {0}'.format(sshot_src))
					
					#self.log.info('dir_name: {0}'.format(dir_name))
					if not os.path.exists(dir_name):
						os.makedirs(dir_name)
						
					#self.file_download(tor_src, '{0}/{1}.{2}'.format(dir_name, title, self.get_extension(tor_src)))
					#self.file_download(poster_src, '{0}/{1}_poster.{2}'.format(dir_name, title, self.get_extension(poster_src)))
					if(self.file_download(sshot_src, '{0}/{1}_screenshot.{2}'.format(dir_name, title, self.get_extension(sshot_src))) < 0): return
				'''
				

	def page_load_text(self, url):
	
		# CAPCHA 페이지 로딩
		self.driver.get(self.human_check_url)
		for i in range(1, 8):
			self.log.info ('Page loading waiting... {0} / {1}'.format(i, self.human_check_url))
			sleep(1)
		self.driver.find_element_by_xpath('/html/body/div/div/a').click()
		for i in range(1, 15):
			self.log.info ('Input CAPCHA waiting... {0}'.format(i))
			sleep(1)
	
	
		self.driver.get(url)
		item_html = self.driver.page_source
		item_soup = BeautifulSoup(item_html, 'html.parser')
		
		
		tlines = item_soup.find('table', {'class':'lista-rounded'}).find('tbody').find_all('tr', recursive=False)[1].find('table').find('tbody').find_all('tr', recursive=False)
		for tline in tlines:
			if(tline.find('td').get_text().strip() == 'Torrent:'):
				tor_src = self.base_url + tline.find('td', {'class':'lista'}).find('a')['href']
				self.log.info('Torrent    : {0}'.format(tor_src))
			elif(tline.find('td').get_text().strip() == 'Poster:'):
				poster_src = tline.find('td', {'class':'lista'}).find('img')['src']
				self.log.info('Poster     : {0}'.format(poster_src))
			elif(tline.find('td').get_text().strip() == 'Description:'):
				sshot_url = tline.find('td', {'class':'lista'}).find('a')['href']
				self.log.info('URL        : {0}'.format(sshot_url))


def show_help():
	print('Usage: {0} <date> <type> <page_num>'.format(sys.argv[0]))
	print('     <date> format: yyyy-mm-dd')
	print('     <type> : s(creenshot) / t(orrent)')

				
if __name__ == '__main__':
	if (len(sys.argv) < 3 or len(sys.argv) > 5):
		show_help()
		sys.exit(0)
		
	if (sys.argv[2] == 's'):
		type = 'ScreenShot'
	elif (sys.argv[2] == 't'):
		type = 'Torrent'
	elif (sys.argv[2] == 'r'):
		type = 'Retrieve'
	else:
		show_help()
		sys.exit()
	
	bjrt = RBTorrentTrawler()
	bjrt.init_driver()

	page = 1
	start_post = None
	if (len(sys.argv) >= 4):
		page = int(sys.argv[3])
	if (len(sys.argv) == 5):
		start_post = sys.argv[4]

	date = sys.argv[1]

	bjrt.get_torrent_seeds(page, date, start_post, type)

	#bjrt.page_load_text('http://rarbg.is/torrent/thyuz9m')

	
