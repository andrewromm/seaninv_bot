from firebase import firebase

firebase = firebase.FirebaseApplication('https://seanbot.firebaseio.com/')

def get_traders():
	return firebase.get('/', name='traders')

def get_trader_by_tg(telegram):
	traders = get_traders()
	return [trader for trader in traders if trader['telegram'] == telegram]

def add_new_trade(telegram, symbol, direction, volume):
	data = {
		'telegram': f'\"{telegram}\"',
		'symbol': symbol,
		'direction': direction,
		'volume': volume
	}
	firebase.post('/trades', data=data)

	
if __name__ == '__main__':
	print(get_trader_by_tg('151174105'))