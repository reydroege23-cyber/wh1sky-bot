from database import EconomyDatabase
import os

p = 'test_repro.db'
fp = 'data/' + p

if os.path.exists(fp):
	os.remove(fp)

db = EconomyDatabase(p)
uid = 123456789

print('before:', db.get_balance(uid))
db.add_balance(uid, 900)
print('after:', db.get_balance(uid))
