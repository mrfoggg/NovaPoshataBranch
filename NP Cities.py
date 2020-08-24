import json
import requests
import pyperclip
from prettytable import PrettyTable
import os
import string
import datetime
import time
import textwrap

api_key = ''
url = 'https://api.novaposhta.ua/v2.0/json/'
width = 90

clear = lambda: os.system('clear')

# функция запроса города с которого доставка

def FindCities(InputCityName, api_key):
	request_dict = {
	"apiKey": api_key,
	"modelName": "Address",
	"calledMethod": "searchSettlements",
	"methodProperties": {
	"CityName": InputCityName,
	"Limit": 50
	}
	}

	request_json = json.dumps(request_dict, indent = 4)

	headers= {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36', 'Content-Type': 'application/json; charset=utf-8'}

	response = requests.post(url, data = request_json)

	response_dict = json.loads(response.text)

	# clear()
	print('\033[1m', "Результат поиска населенного пункта по запросу '", InputCityName, "':", '\033[0m')
	print()
	print("Ответ сервера:", "Успешно -", response_dict["success"])
	print()

	response_data = response_dict["data"]

	print("Результатов поиска: ", response_data[0]["TotalCount"])

	adresses = response_data[0]["Addresses"]

	x = PrettyTable ()
	x.field_names = [ "№ / п.", "Название города", "Область", "Район", "Кол-во отд."]
	x.align [ "Название города" ] = "l"
	x.align [ "Область" ] = "l"
	x.align [ "Район" ] = "l"

	city = []
	i = 0
	while i < len(adresses):

		x.add_row([i+1, textwrap.fill(adresses[i]['MainDescription'], 25), adresses[i]['Area'], adresses[i]['Region'], adresses[i]['Warehouses']])
		city.append({'name': adresses[i]['MainDescription'], 'Area': adresses[i]['Area'], 'Region': adresses[i]['Region'], 'ref': adresses[i]['Ref'], 'Warehouses': adresses[i]['Warehouses'], 'ref_from': adresses[i]["DeliveryCity"]})
		i += 1
	print(x)
	return city

def DeliveryDate(ServiceType, CityRecipient, CitySender, Cityname, CityTOname, apiKey, *delta):
	print('расчет срока доставки из', Cityname, "в ", CityTOname)
	for i in delta:
		date = datetime.date.today() + datetime.timedelta(days=i)
		data_for_date =  {
		"apiKey": api_key,
		"modelName": "InternetDocument",
		"calledMethod": "getDocumentDeliveryDate",
		"methodProperties": {
		# "DateTime": str(date.day) + '.' + str(date.month) + '.' + str(date.year),
		"DateTime": date.strftime("%d.%m.%Y"),
		"ServiceType": ServiceType,
		"CitySender": CitySender,
		"CityRecipient": CityRecipient
		}
		}
		data_for_date_json = json.dumps(data_for_date, indent = 4)
		url = 'https://api.novaposhta.ua/v2.0/json/'
		response = requests.post(url, data = data_for_date_json)
		response_dict = json.loads(response.text)
		response_data = response_dict['data'][0]
		DeliveryDate_notFormated = response_data['DeliveryDate']['date']
		DeliveryDate = DeliveryDate_notFormated.split()[0]
		# DeliveryDateWithPoint = DeliveryDate.replace("-", ".")
		DeliveryDateDateformate = datetime.datetime.strptime(DeliveryDate, "%Y-%m-%d")
		print("В случае отправки %s (%s) дата прибытия будет: " % (date, date.isoweekday()), DeliveryDateDateformate.strftime("%Y-%m-%d"), "(%s)"%DeliveryDateDateformate.isoweekday())
		# "(%s)"%DeliveryDateDateformate.isoweekday()

def DeliveryCost(ServiceType, CityRecipient, CitySender, m, v, price, SeatsAmount, apiKey):
	# m = int(input("Введите вес посылки: \t"))
	# v = float(input("Введите объем посылки: \t"))
	# price = int(input("Введите стоимость посылки: \t"))
	# SeatsAmount = int(input("Введите количество мест: \t"))
	vm = v * 250
	if vm > m:
		m = str(vm)
	else:
		m = str(m)
	dataCost = {
	"modelName": "InternetDocument",
	"calledMethod": "getDocumentPrice",
	"methodProperties": {
		"CitySender": CitySender,
		"CityRecipient": CityRecipient,
		"Weight": m,
		"ServiceType": ServiceType,
		"Cost": str(price),
		"CargoType": "Cargo",
		"SeatsAmount": SeatsAmount,
		"RedeliveryCalculate": {
		"CargoType": "Money",
		"Amount": str(price)
	}
	},
   "apiKey": apiKey
	}

	dataCost_json = json.dumps(dataCost, indent = 4)
	url = 'https://api.novaposhta.ua/v2.0/json/'
	response = requests.post(url, data = dataCost_json)
	response_dict = json.loads(response.text)
	return response_dict['data'][0]["Cost"]

def find_city_from(api_key, city_detail): 
	request_city_from_dict = {
	"modelName": "Address",
	"calledMethod": "getCities",
	"methodProperties": {
	"Ref": city_detail['ref_from']
	},
	"apiKey": api_key
	}

	request_city_from_json = json.dumps(request_city_from_dict, indent = 4)

	response_city_from = requests.post(url, data = request_city_from_json)

	response_city_from_dict = json.loads(response_city_from.text)
	response_city_from_data = response_city_from_dict["data"][0]
	print("В населенном пункте '%s' нет отделений" % city_detail['name'])
	print("Возможна адресная доставка из населенного пункта:", response_city_from_data["Description"])
	print()
	print("В буфер обмена скопирована строка:")
	adress_to_copy = 'Курьерск. дост. НП из "%s" в "%s" по адресу: ' % (response_city_from_data["Description"], city_detail['name'])
	print('\033[1m', adress_to_copy, '\033[0m')
	pyperclip.copy(adress_to_copy)
	want_date = input("\033[1m Желаете расчитать дату прибытия? \033[0m \n\t0 - да, из Харькова, \n\t1 - да, из другого города, \n\tEnter- нет\n")
	if want_date == "0":
		DeliveryDate("WarehouseDoors", city_detail['ref'], 'e71f8842-4b33-11e4-ab6d-005056801329', 'Харьков', city_detail['name'], api_key, 0, 1, 2, 3, 4,)
		print()
		m = float(input("Введите вес посылки: \t"))
		v = float(input("Введите объем посылки: \t"))
		price = int(input("Введите стоимость посылки: \t"))
		SeatsAmount = int(input("Введите количество мест: \t"))
		print()
		nlg = float(20 + price * 0.02)
		print("\033[1m Комиссия за перевод денег составляет: %s грн \033[0m" %  nlg)
		print()
		print("\033[1m Доставка на отделение:\033[0m")
		cost = DeliveryCost('WarehouseWarehouse', city_detail['ref'], 'e71f8842-4b33-11e4-ab6d-005056801329', m, v, price, SeatsAmount,api_key)
		print("Стоимость доставки без наложки составляет %s грн" % cost)
		print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost) + nlg))
		print()
		cost2 = DeliveryCost("WarehouseDoors", city_detail['ref'], 'e71f8842-4b33-11e4-ab6d-005056801329', m, v, price, SeatsAmount,api_key)
		print("\033[1m Доставка на адрес:\033[0m")
		print("Стоимость доставки без наложки составляет %s грн" % cost2)
		print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost2) + nlg))

	elif want_date == "1":
		InputCityName = input("Введите часть названия искомого населенного пункта откуда будет доставка(или 0 чтобы выйти): \n \t")
		citiesFrom = FindCities(InputCityName, api_key)
		cityFromChoose = input("Выберете город откуда будет доставка (0 прервать расчет срока доставки):\n")
		cityFrom = citiesFrom[int(cityFromChoose)-1]
		DeliveryDate('WarehouseWarehouse', city_detail['ref'], cityFrom['ref'], cityFrom['name'], city_detail['name'], api_key, 0, 1, 2, 3, 4,)
		print()
		m = float(input("Введите вес посылки: \t"))
		v = float(input("Введите объем посылки: \t"))
		price = int(input("Введите стоимость посылки: \t"))
		SeatsAmount = int(input("Введите количество мест: \t"))
		print()
		nlg = float(20 + price * 0.02)
		print("\033[1m Комиссия за перевод денег составляет: %s грн \033[0m" %  nlg)
		print()
		print("\033[1m Доставка на отделение:\033[0m")
		cost = DeliveryCost('WarehouseWarehouse', city_detail['ref'], cityFrom['ref'], m, v, price, SeatsAmount,api_key)
		print("Стоимость доставки без наложки составляет %s грн" % cost)
		print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost) + nlg))
		print()
		cost2 = DeliveryCost("WarehouseDoors", city_detail['ref'], cityFrom['ref'], m, v, price, SeatsAmount,api_key)
		print("\033[1m Доставка на адрес:\033[0m")
		print("Стоимость доставки без наложки составляет %s грн" % cost2)
		print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost2) + nlg))

def find_street(adresses):
	warh_num = ''
	while warh_num == '':
		street_name = (input("Введите часть названия улицы:\n \t")).lower()
		a = PrettyTable ()
		a.field_names = [ "№ отделения", "Номер и адрес отделения"]
		a.align [ "Номер и адрес отделения" ] = "l"
		for adr in adresses:
			if ((adresses[adr]['name']).lower()).find(street_name) != -1:
				a.add_row([adr, textwrap.fill(adresses[adr]['name'], width)])
		print(a)
		warh_num = input("Выберите номер отделения или нажмите ентер для повторного поиска по названию улицы:\n \t")
	return warh_num


InputCityName = ""
while InputCityName != "0":
	print('\033[1m', "\tПОИСК НАСЕЛЕННОГО ПУНКТА", '\033[0m')
	try:
		InputCityName = input("Введите часть названия искомого населенного пункта (или 0 чтобы выйти): \n \t")
		city = FindCities(InputCityName, api_key)

		# выбор города для отображения отделений
		city_detail_id = ""
		print()
		print('\033[1m', "\tПОИСК ОТДЕЛЕНИЯ В НАСЕЛЕННОМ ПУНКТЕ", '\033[0m',)
		city_detail_id = input("Для получения списка отделений введите порядковый номер населенного пункта из таблицы выше.\nДля населенных пунктов без отделений покажет город из которого обудет адресная доставка\n(или нажмите Enter для повторного поиска населенного пункта):\n \t")

		if city_detail_id != "":
			city_detail = city[int(city_detail_id)-1]

			if city_detail['Warehouses'] == 0:
				find_city_from(api_key, city_detail)
			else:
				requests_get_adress = {
			    "modelName": "AddressGeneral",
			    "calledMethod": "getWarehouses",
			    "methodProperties": {
				"SettlementRef": city_detail['ref']},
			    "apiKey": api_key
				}
				requests_get_adress_json = json.dumps(requests_get_adress, indent = 4)
				response_get_adress = requests.post(url, data = requests_get_adress_json)
				response_get_adress_dict = json.loads(response_get_adress.text)
				adress_datas = response_get_adress_dict['data']

				y = PrettyTable ()
				y.field_names = [ "№ отделения", "Номер и адрес отделения"]
				y.align [ "Номер и адрес отделения" ] = "l"
				if len(adress_datas) > 0:
					j = 0
					adresses = {}

					while j < len(adress_datas):
						y.add_row([adress_datas[j]['Number'], textwrap.fill(adress_datas[j]['Description'], width)])
						adresses[adress_datas[j]['Number']] = {'name': adress_datas[j]["Description"], "PostFinance": adress_datas[j]["PostFinance"], "POSTerminal": adress_datas[j][ "POSTerminal"], 'TotalMaxWeightAllowed': adress_datas[j]['TotalMaxWeightAllowed'], "PlaceMaxWeightAllowed": adress_datas[j]["PlaceMaxWeightAllowed"], "Schedule": adress_datas[j]["Schedule"], "Reception": adress_datas[j]["Reception"], "Delivery": adress_datas[j]["Delivery"]
						}
						
						j+=1

					# clear()
					print('\033[1m', "Список отделений в населенном пункте %s (%s обл., %s р-н)" % (city_detail['name'], city_detail['Area'], city_detail['Region']), '\033[0m')
					print(y)
					# print(city_detail['ref'])

					# выбор отделения для отображения деталей
					want_date = "2"
					while want_date == "2":
						adress_id = input("Введите номер отделения для получения деталей или 0 для отбора отделений по названию улиц:\n \t")
						if adress_id == '0':
							adress_id = find_street(adresses)
						adr = adresses[adress_id]
						# clear()         
						warh_full_info = "%s (%s обл., %s р-н), %s" %(city_detail['name'], city_detail['Area'], city_detail['Region'], adr['name'])
						print('\033[1m', "Населененный пункт", warh_full_info, '\033[0m',)
						print()

						if adr["PostFinance"] == '1':
							print("\t- Филиал PostFinance имеется")
						else:
							print("\t- Филиал PostFinance отсутствует")				
						if adr["POSTerminal"] == '1':
							print("\t- Банковский терминал для оплаты картой имеется")
						else:
							print("\t- Банковский терминал для оплаты картой отсутствует")
						print("\t- Максимальный общий вес посылки: %s" % adr['TotalMaxWeightAllowed'])
						print("\t- Максимальный вес одного места: %s" % adr['PlaceMaxWeightAllowed'])
						print()
						print('\033[1m', "\tГрафик отделения:" , '\033[0m',)

						z = PrettyTable ()
						z.field_names = ["День недели", "Режим работы", "График прихода посылок", "График отправки день в день"]
						z.align["День недели"] = 'r'
						z.add_row(['Понедельник', adr["Schedule"]['Monday'], adr["Reception"]['Monday'], adr["Delivery"]['Monday']])
						z.add_row(['Вторник', adr["Schedule"]['Tuesday'], adr["Reception"]['Tuesday'], adr["Delivery"]['Tuesday']])
						z.add_row(['Среда', adr["Schedule"]['Wednesday'], adr["Reception"]['Wednesday'], adr["Delivery"]['Wednesday']])
						z.add_row(['Четверг', adr["Schedule"]['Thursday'], adr["Reception"]['Thursday'], adr["Delivery"]['Thursday']])
						z.add_row(['Пятница', adr["Schedule"]['Friday'], adr["Reception"]['Friday'], adr["Delivery"]['Friday']])
						z.add_row(['Суббота', adr["Schedule"]['Saturday'], adr["Reception"]['Saturday'], adr["Delivery"]['Saturday']])
						z.add_row(['Воскресенье', adr["Schedule"]['Sunday'], adr["Reception"]['Sunday'], adr["Delivery"]['Sunday']])
						print(z)
						print()
						print('\033[1m', '\t В буфер обмена скопирована строка:', '\033[0m')
						adress = adr['name'].replace("Пункт приймання-видачі", "пункт прийм./вид. №1").replace("Відділення", "отд.").replace(" на одне місце", "/место.")


						if adress.find("№") == -1:
							adress = adress.replace("отд.", "отд. № %s" % adress_id)

						# adress.replace("отд.", "отд. № %s" % adress_id)

						# adress = adress.replace("Відділення", "отд.")
						# adress = adress['name'].replace(" на одне місце", "/место.")
						if city_detail['Region']!="" and city_detail['Region']!=" ":
							copy_adress_string = "%s (%s обл., %s р-н), НП %s" % (city_detail['name'], city_detail['Area'], city_detail['Region'], adress)
						else:
							copy_adress_string = "%s (%s обл.), НП %s" % (city_detail['name'], city_detail['Area'], adress)
						print(copy_adress_string)
						pyperclip.copy(copy_adress_string)
						print()

						want_date = input("\033[1m Желаете расчитать дату прибытия? \033[0m \n\t0 - да, из Харькова, \n\t1 - да, из другого города, \n\tEnter- нет\n\t2 - Выбрать другое отделение\n")
						if want_date == "0":
							DeliveryDate('WarehouseWarehouse', city_detail['ref'], 'e71f8842-4b33-11e4-ab6d-005056801329', 'Харьков', city_detail['name'],api_key, 0, 1, 2, 3, 4,)
							print()
							want_cost = input("\033[1m Желаете расчитать стоимость доставки из Харькова? \033[0m \n\t0 - да \n\tEnter- нет\n\t")
							if want_cost == "0":
								print()
								m = float(input("Введите вес посылки: \t"))
								v = float(input("Введите объем посылки: \t"))
								price = int(input("Введите стоимость посылки: \t"))
								SeatsAmount = int(input("Введите количество мест: \t"))
								print()
								nlg = float(20 + price * 0.02)
								print("\033[1m Комиссия за перевод денег составляет: %s грн \033[0m" %  nlg)
								print()
								print("\033[1m Доставка на отделение:\033[0m")
								cost = DeliveryCost('WarehouseWarehouse', city_detail['ref'], 'e71f8842-4b33-11e4-ab6d-005056801329', m, v, price, SeatsAmount,api_key)
								print("Стоимость доставки без наложки составляет %s грн" % cost)
								print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost) + nlg))
								print()
								cost2 = DeliveryCost("WarehouseDoors", city_detail['ref'], 'e71f8842-4b33-11e4-ab6d-005056801329', m, v, price, SeatsAmount,api_key)
								print("\033[1m Доставка на адрес:\033[0m")
								print("Стоимость доставки без наложки составляет %s грн" % cost2)
								print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost2) + nlg))

						elif want_date == "1":
							InputCityName = input("Введите часть названия искомого населенного пункта (или 0 чтобы выйти): \n \t")
							citiesFrom = FindCities(InputCityName, api_key)
							cityFromChoose = input("Выберете город откуда будет доставка (0 прервать расчет срока доставки):\n")
							cityFrom = citiesFrom[int(cityFromChoose)-1]
							DeliveryDate('WarehouseWarehouse', city_detail['ref'], cityFrom['ref'], cityFrom['name'], city_detail['name'], api_key, 0, 1, 2, 3, 4,)
							print()
							want_cost = input("\033[1m Желаете расчитать стоимость доставки из %s в %s? \033[0m \n\t0 - да \n\tEnter- нет\n\t"%(cityFrom['name'], city_detail['name']))
							if want_cost == "0":
								print()
								m = float(input("Введите вес посылки: \t"))
								v = float(input("Введите объем посылки: \t"))
								price = int(input("Введите стоимость посылки: \t"))
								SeatsAmount = int(input("Введите количество мест: \t"))
								print()
								nlg = float(20 + price * 0.02)
								print("\033[1m Комиссия за перевод денег составляет: %s грн \033[0m" %  nlg)
								print()
								print("\033[1m Доставка на отделение:\033[0m")
								cost = DeliveryCost('WarehouseWarehouse', city_detail['ref'], cityFrom['ref'], m, v, price, SeatsAmount,api_key)
								print("Стоимость доставки без наложки составляет %s грн" % cost)
								print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost) + nlg))
								print()
								cost2 = DeliveryCost("WarehouseDoors", city_detail['ref'], cityFrom['ref'], m, v, price, SeatsAmount,api_key)
								print("\033[1m Доставка на адрес:\033[0m")
								print("Стоимость доставки без наложки составляет %s грн" % cost2)
								print("Стоимость доставки с наложеным платежом составляет %s грн" % (float(cost2) + nlg))


						elif want_date == "2":
							print(y)

						
				else:
					print('\033[91m', "Все отделения закрылись", '\033[0m')
					find_city_from(api_key, city_detail)



		else:
			print('\033[1m', "Повторный поиск города", '\033[0m')	
	except:
		print('\033[91m', "Не найдено", '\033[0m')

	print()
	print("=================================================================================")
	print()
