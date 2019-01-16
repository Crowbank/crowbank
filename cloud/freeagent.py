import requests
import sys
import re
import argparse
import logging
from crowbank.petadmin import Environment
from datetime import datetime


# from crowbank.fb_reviews import sql
# from _sqlite3 import sqlite_version

# headers = { 'Authorization: Bearer 1huYkz44prHdcK89cc7YccEDf8IelgSFK_-hTKAHE', }

base = 'https://api.freeagent.com/v2/'

log = logging.getLogger(__name__)

class FreeAgent:
    def __init__(self):
        self.parameters = {}
        self.items = {}
        self.bank_accounts = []
        self.transactions = []
        self.journals = []
        self.connection = None
        self.platform = sys.platform
        self.env = Environment('prod')

    def read_parameters(self):
        cur = self.env.get_cursor()
        sql = 'select api_key, api_value from tblfreeagent_api'
        cur.execute(sql)
        for row in cur:
            self.parameters[row[0]] = row[1]
    
    def refresh_access_token(self):
        data = {'client_secret' : self.parameters['oauth_secret'],
                                     'grant_type' : 'refresh_token',
                                     'refresh_token' : self.parameters['refresh_token'],'client_id' : self.parameters['oauth_identifier']}
        
        resp = requests.post(base + 'token_endpoint', data=data, auth=requests.auth.HTTPBasicAuth(self.parameters['oauth_identifier'], self.parameters['oauth_secret']))
        
        if resp.status_code == 200:
            self.parameters['access_token'] = resp.json()['access_token']
            sql = "update tblfreeagent_api set api_value = '%s' where api_key = 'access_token'" % self.parameters['access_token']
            self.env.execute(sql)
    
    # Equivalent curl call:
    # curl -H 'Authorization: Bearer XXX' -H 'Accept: application/json' -H 'Content-Type: application/json' -X GET/PUT/POST/DELETE [-data '{...}']
    def request(self, url, params = {}):
        headers = { 'Authorization': 'Bearer %s' % self.parameters['access_token'] }
        if url[:8] != self.parameters['base_url'][:8]:
            url = self.parameters['base_url'] + url
        log.debug('sending request with %s' % params)
        resp = requests.get(url, headers=headers, params=params)
        resp = resp.json()
        return resp
    
    def post(self, url, data = {}):
        headers = { 'Authorization': 'Bearer %s' % self.parameters['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json' }
        if url[:8] != self.parameters['base_url'][:8]:
            url = self.parameters['base_url'] + url
        log.info('sending POST with %s' % data)
        resp = requests.post(url, headers=headers, json=data)
        resp = resp.json()
        return resp

    def put(self, url, data = {}):
        headers = { 'Authorization': 'Bearer %s' % self.parameters['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json' }
        if url[:8] != self.parameters['base_url'][:8]:
            url = self.parameters['base_url'] + url
        log.info('sending PUT with %s' % data)
        resp = requests.put(url, headers=headers, json=data)
        resp = resp.json()
        return resp

    def delete(self, url):
        headers = { 'Authorization': 'Bearer %s' % self.parameters['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json' }
        if url[:8] != self.parameters['base_url'][:8]:
            url = self.parameters['base_url'] + url
        log.info('sending DELETE to %s' % url)
        resp = requests.delete(url, headers=headers)
        return resp
        

class FreeAgentItem(object):
    items = []
    by_url = {}
    
    @classmethod
    def adorn(cls, name):
        return cls.db_prefix + name
    
    @classmethod
    def strip(cls, name):
        return name.replace(cls.db_prefix, '')    
    
    @classmethod
    def read(cls, env):
        sql = "Select %s from %s" % (", ".join(map(cls.adorn, cls.db_types.keys())), cls.db_table)
        cur = env.get_cursor()
        cur.execute(sql)
        cls.items = [cls({key : value for (key, value) in zip(cls.db_types.keys(), row)}) for row in cur]
        return cls.items

    @classmethod
    def process_download_responds(cls, resp, context = ''):
        items = resp[cls.item_name]
        msg = 'reading %d %s items' % (len(items), cls.class_name)
        if context:
            msg = '%s: %s' % (context, msg)
        if items:
            log.info(msg)
        else:
            log.debug(msg)
        return items
        
        
    @classmethod
    def download(cls, fa, write=True, params={}):
        log.debug('downloading %s. {%s}' % (cls.item_name, params))
        page = 1
        cont = True
        items = []
        if not fa.parameters:
            fa.read_parameters()
        
        while cont:
            params.update( {'page' : page, 'per_page' : 100} )
            url = fa.parameters['base_url'] + cls.item_name
            resp = fa.request(url, params)
            if 'errors' in resp:
                log.error(resp['errors'])
                if 'error' in resp['errors'] and resp['errors']['error']['message'] == 'Access token not recognised':
                    fa.refresh_access_token()
                    log.info ('Refreshed access token')
                    cls.download(fa, params)
                else:
                    log.error ('Unknown error')
                    return
            context_items = []
            if 'bank_account' in params:
                context_items.append('account - %s' % BankAccount.by_url[params['bank_account']].name)
            if page > 1:
                context_items.append('page - %d' % page)
            new_items = cls.process_download_responds(resp, ', '.join(context_items)) 
            items += new_items
            log.debug ("Loaded page %d of %s" % (page, cls.class_name))
            page += 1
            if len(new_items) < 100 or not cls.is_paged:
                cont = False
        
        mapped = list(map(cls, items))
        if mapped:
            log.info('finished downloading %d %s items' % (len(mapped), cls.class_name))
            for item in mapped:
                cls.by_url[item.url] = item
        else:
            log.debug('finished downloading %d %s items' % (len(mapped), cls.class_name))
        cls.items = mapped
        
        if write:
            cls.write_all(fa.env)
        return mapped
    
    @classmethod
    def write_all(cls, env):
        for item in cls.items:
            item.write(env)
        
        n = str(datetime.now())[:19]
        sql = "execute fa_update_download '%s', '%s'" % (cls.class_name, n)
        env.execute(sql)
        
    def __init__(self, response):
        self.dict = response
        if not 'id' in response:
            if 'url' in response:
                m = re.match(r'.*/(\d+)$', self.dict['url'])
                self.id = int(m.group(1))
                self.dict['id'] = self.id
        
    def __getattr__(self, name):
        if name in self.dict:
            return self.dict[name]
        else:
            return None
        
    def write(self, env):
        sql = "select count(*) from %s where %sid = %d" % (self.db_table, self.db_prefix, self.id)
        cur = env.get_cursor()
        cur.execute(sql)
        for row in cur:
            c = row[0]
        
        if c > 0:
            sql = "delete from %s where %sid = %d" % (self.db_table, self.db_prefix, self.id)
            env.execute(sql)
            
        keys = list(set(self.db_types.keys()) & set(self.dict.keys()))
        fields = list(map(self.adorn, keys))
        sql = "insert into %s (%s) values (" % (self.db_table, ", ".join(fields))
        values = []
        for k in keys:
            v = self.dict[k]
            db_type = self.db_types[k]
            if db_type in ['string', 'date', 'datetime']:
                values.append("'%s'" % v.replace("'", "''"))
            elif db_type == 'boolean':
                values.append('1' if v else '0')
            else:
                values.append(str(v))
        sql += ', '.join(values)
        sql += ')'
        env.execute(sql)
    
    def download_one(self, fa):
        fa.request(self.url)
        

class Category(FreeAgentItem):
    is_paged = False
    class_name = 'Category'
    item_name = 'categories'
    db_table = 'fa_category'
    db_prefix = 'fac_'
    db_types = {
        'id' : 'int',
        'url' : 'string',
        'description' : 'string',
        'nominal_code' : 'string',
        'group_description' : 'string',
        'auto_sales_tax_rate' : 'string',
        'allowable_for_tax' : 'boolean',
        'tax_reporting_name' : 'string',
        'category_type' : 'string'
    }
    
    @classmethod
    def process_download_responds(cls, resp):
        def app(key, val):
            val2 = dict(val)
            val2['category_type'] = key
            return val2
        
        items = []
        for (key, val) in resp.items():
            items += [app(key, item) for item in val]
        return items
    
    
class User(FreeAgentItem):
    is_paged = True
    class_name = 'User'
    item_name = 'users'
    db_table = 'fa_user'
    db_prefix = 'fau_'
    db_types = {
        'id' : 'int',
        'url' : 'string',
        'email' : 'string',
        'first_name' : 'string',
        'last_name' : 'string',
        'ni_number' : 'string',
        'unique_tax_reference' : 'string',
        'role' : 'string',
        'opening_mileage' : 'decimal',
        'hidden' : 'boolean',
        'send_invitation' : 'boolean',
        'permission_level' : 'int',
        'created_at' : 'datetime',
        'updated_at' : 'datetime',
        'existing_password' : 'string',
        'password' : 'string',
        'password_confirmation' : 'string'
        }


class BankAccount(FreeAgentItem):
    is_paged = False
    class_name = 'BankAccount'
    item_name = 'bank_accounts'
    db_table = 'fa_bankaccount'
    db_prefix = 'ba_'
    db_types = {
        'id' : 'int',
        'url' : 'string',
        'type' : 'string',
        'name' : 'string',
        'currency' : 'string',
        'is_personal' : 'boolean',
        'is_primary' : 'boolean',
        'status' : 'string',
        'bank_name' : 'string',
        'opening_balance' : 'money',
        'bank_code' : 'string',
        'current_balance' : 'money',
        'latest_activity_date' : 'date',
        'created_at' : 'datetime',
        'updated_at' : 'datetime',
        'account_number' : 'string',
        'sort_code' : 'string',
        'secondary_sort_code' : 'string',
        'iban' : 'string',
        'bic' : 'string',
        'email' : 'string'
    }


class BankTransactionExplanation(FreeAgentItem):
    is_paged = True
    class_name = 'BankTransactionExplanation'
    item_name = 'bank_transaction_explanation'
    db_table = 'fa_bankexplanation'
    db_prefix = 'fabe_'
    db_types = {
        'id' : 'int',
        'url' : 'string',
        'bank_account' : 'string',
        'bank_transaction' : 'string',
        'type' : 'string',
        'ec_status' : 'string',
        'place_of_supply' : 'string',
        'dated_on' : 'date',
        'gross_value' : 'money',
        'transfer_value' : 'money',
        'sales_tax_rate' : 'decimal',
        'sales_tax_value' : 'money',
        'manual_sales_tax_amount' : 'money',
        'description' : 'string',
        'detail' : 'string',
        'category' : 'string',
        'cheque_number' : 'string',
        'marked_for_review' : 'boolean',
        'is_money_in' : 'boolean',
        'is_money_out' : 'boolean',
        'is_money_paid_to_user' : 'boolean',
        'is_locked' : 'boolean',
        'has_pending_operation' : 'boolean',
        'locked_reason' : 'string',
        'project' : 'string',
        'rebill_type' : 'string',
        'rebill_factor' : 'decimal',
        'receipt_reference' : 'string',
        'paid_invoice' : 'string',
        'foreign_currency_value' : 'money',
        'paid_bill' : 'string',
        'paid_user' : 'string',
        'linked_transfer_account' : 'string',
        'linked_transfer_explanation' : 'string',
        'stock_item' : 'string',
        'stock_altering_quantity' : 'int',
        'asset_life_years' : 'int',
        'disposed_asset' : 'string',
        'uploaded_at' : 'datetime'
    }
    
    db_upload_types = {
        'id' : 'int',
        'url' : 'string',
        'bank_transaction' : 'string',
        'type' : 'string',
        'dated_on' : 'date',
        'gross_value' : 'money',
        'sales_tax_rate' : 'decimal',
        'sales_tax_value' : 'money',
        'description' : 'string',
        'detail' : 'string',
        'category' : 'string',
        'marked_for_review' : 'boolean',
        'is_money_in' : 'boolean',
        'is_money_out' : 'boolean',
        'is_money_paid_to_user' : 'boolean',
        'receipt_reference' : 'string',
        'foreign_currency_value' : 'money',
        'paid_bill' : 'string',
        'paid_user' : 'string',
        'linked_transfer_account' : 'string',
        'asset_life_years' : 'int',
        'transfer_value' : 'money',
        'transfer_bank_account_id' : 'int'
        }

    @classmethod
    def download(cls, fa, write=True, params={}):
        log.debug('downloading %s. {%s}' % (cls.item_name, params))
        n = str(datetime.now())[:19]
        explanations = []
        if not BankTransaction.items:
            BankTransaction.download(fa, False, params)
        for t in BankTransaction.items:
            explanations += t.bank_transaction_explanations
        for e in explanations:
            e.dict['uploaded_at'] = n 
        
        cls.items = explanations
        if write:
            cls.write_all(fa.env)
        return explanations     

    @classmethod
    def read_uploads(cls, fa, force=False):
        sql = 'select ' + cls.db_prefix + 'no, ' + ', '.join(map(cls.adorn, cls.db_upload_types.keys())) + ' from vw_fa_bank_explanation_upload'
        if not force:
            sql = sql + ' where fabe_uploaded_at is null'
        sql = sql + ' order by fabe_no'
        cur = fa.env.get_cursor()
        cur.execute(sql)
        items = {}
        for row in cur:
            no = row[0]
            i = 1
            d = {'no' : no}
            for k in cls.db_upload_types:
                d[k] = row[i]
                i = i + 1
                
            item = BankTransactionExplanation(d)
            items[no] = item
        
        return items      
        
        
    @classmethod
    def upload_all(cls, fa, force=False):
        items = cls.read_uploads(fa, force)
        redownload_transactions = set()
        for item in items.values():
            item.upload(fa)
            redownload_transactions.add(item.bank_transaction)
        
        for url in redownload_transactions:
            resp = fa.request(url)
            if 'bank_transaction' in resp and 'bank_transaction_explanations' in resp['bank_transaction']:
                d = resp['bank_transaction']
                sql = "Execute pclear_explanations '%s'" % d['url']
                fa.env.execute(sql)
                for d in resp['bank_transaction']['bank_transaction_explanations']:
                    x = BankTransactionExplanation(d)
                    x.write(fa.env)
                    
            
            
    def upload(self, fa):
        d = {k : v for (k, v) in self.dict.items() if v != None}
        data = {'bank_transaction_explanation' : d}
        if self.id:
            url = 'bank_transaction_explanations/%d' % self.id
            resp = fa.put(url, data)
            me = 'Id %d' % self.id
        elif self.url:
            resp = fa.delete(self.url)
            sql = "Execute pdelete_fa_bankexplanation '%s'" % self.url
        else:
            url = 'bank_transaction_explanations'
            resp = fa.post(url, data)
            if self.no:
                me = 'No %d' % self.no
            elif self.dict['bank_transaction']:
                me = 'Tran %s' % self.dict['bank_transaction']
            else:
                me = 'An Explanation'
        if resp:
            if 'error' in resp or 'errors' in resp:
                log.error('Error uploading %s' % me)
                if 'error' in resp:
                    log.error(resp['error'])
                else:
                    for err in resp['errors']:
                        if 'message' in err:
                            log.error(err['message'])
            elif self.no:
                sql = 'execute pmark_bankexplanation_uploaded %d' % self.no
                fa.env.execute(sql)
        return resp
                    

class BankTransaction(FreeAgentItem):
    is_paged = True
    class_name = 'BankTransaction'
    item_name = 'bank_transactions'
    db_table = 'fa_banktransaction'
    db_prefix = 'fabt_'
    db_types = {
        'id' : 'int',
        'url' : 'string',
        'amount' : 'money',
        'bank_account' : 'string',
        'dated_on' : 'date',
        'description' : 'string',
        'full_description' : 'string',
        'uploaded_at' : 'datetime',
        'unexplained_amount' : 'money',
        'is_manual' : 'boolean',
        'view' : 'string',
        'created_at' : 'datetime',
        'updated_at' : 'datetime',
        'matching_transactions_count' : 'int'
    }

    views = [
        'unexplained',
        'explained',
        'marked_for_review'
    ]

    @classmethod
    def download(cls, fa, write=True, params={}):
        log.debug('downloading %s. {%s}' % (cls.item_name, params))

        n = str(datetime.now())[:19]
        if not BankAccount.items:
            BankAccount.download(fa, False, params)
        accounts = BankAccount.items

        transactions = []
        for account in accounts:
            params['bank_account'] = account.url
            log.debug('account: %s' % account.name)
            if account.is_primary:
                for v in cls.views:
                    params['view'] = v
                    view_transactions = super().download(fa, False, params)
                    for t in view_transactions:
                        t.dict['view'] = v
                    transactions += view_transactions
            else:
                params['view'] = 'all'
                transactions += super().download(fa, False, params)
        
        for t in transactions:
            t.dict['uploaded_at'] = n
        cls.items = transactions
        
        if write:
            cls.write_all(fa.env)
        return transactions
    
    def __init__(self, response):
        super().__init__(response)
        self.dict['bank_transaction_explanations'] = map(BankTransactionExplanation, self.dict['bank_transaction_explanations'])
    
    def write(self, env):
        super().write(env)
        sql = "delete from fa_bankexplanation where fabe_bank_transaction = '%s'" % self.url
        env.execute(sql)
    

class JournalEntry(FreeAgentItem):
    is_paged = True
    class_name = 'JournalEntry'
    item_name = ''
    db_table = 'fa_journal_entry'
    db_prefix = 'faje_'
    db_types = {
        'id' : 'int',
        'journal_set_id' : 'int',
        'url' : 'string',
        'category' : 'string',
        'debit_value' : 'money',
        'user' : 'string',
        'stock_item' : 'string',
        'stock_altering_quantity' : 'int',
        'bank_account' : 'string',
        'description' : 'string'
    }

    
    @classmethod
    def download(cls, fa, write=True, params={}):
        log.debug('downloading %s. {%s}' % (cls.item_name, params))

        if not JournalSet.items:
            JournalSet.download(fa, False, params)
            
        entries = []
        for s in JournalSet.items:
            for entry in s.journal_entries:
                entry.set_set(s)
            entries += s.journal_entries
        
        cls.items = entries
        if write:
            cls.write_all(fa.env)
            
        return entries
    
    def set_set(self, s):
        self.dict['journal_set_id'] = s.id
    
        
class JournalSet(FreeAgentItem):
    is_paged = True
    class_name = 'JournalSet'
    item_name = 'journal_sets'
    db_table = 'fa_journal_set'
    db_prefix = 'faj_'
    db_types = {
        'id' : 'int',
        'url' : 'string',
        'dated_on' : 'date',
        'description' : 'string',
        'tag' : 'string'
        }
    
    @classmethod
    def upload_all(cls, fa, force=False):
        sql = 'select faj_no, faj_dated_on, faj_description from fa_journal_set_upload'
        if not force:
            sql = sql + ' where faj_uploaded is null'
        cur = fa.env.get_cursor()
        cur.execute(sql)
        items = {}
        for row in cur:
            no = row[0]
            item = JournalSet({'dated_on' : row[1], 'description' : row[2], 'journal_entries' : []})
            item.no = no
            items[no] = item
        
        sql = 'select faje_no, faje_journal_set_no, faje_category, faje_debit_value, faje_user, faje_description from fa_journal_entry_upload'
        if not force:
            sql = sql + ' where faje_uploaded is null'
            
        cur.execute(sql)
        for row in cur:
            no = row[0]
            set_no = row[1]
            entry = {'category' : row[2], 'debit_value' : row[3], 'user' : row[4], 'description' : row[5]}
            if set_no in items.keys():
                items[set_no].dict['journal_entries'].append(entry)
                
        for item in items.values():
            item.upload(fa)
                    
    def __init__(self, response):
        super().__init__(response)
        self.dict['journal_entries'] = list(map(JournalEntry, self.dict['journal_entries']))

    def upload(self, fa):
        data = {'journal_set' : self.dict}

        url = 'journal_sets'
        resp = fa.post(url, data)

        if resp:
            if 'error' in resp or 'errors' in resp:
                log.error('Error uploading no %d' % self.no)
                if 'error' in resp:
                    log.error(resp['error'])
                else:
                    for err in resp['errors']:
                        if 'message' in err:
                            log.error(err['message'])
            elif self.no:
                sql = 'execute pmark_journalset_uploaded %d' % self.no
                fa.env.execute(sql)

        return resp


def download(fa, item_type='variables', asof=None, do_write=True, force=False, skip_db=False):
    log.info('running download')
       
    params = {}
    
    if not item_type:
        item_type = 'variables'
        
    if not force and item_type in ('transactions', 'all', 'variables') and not asof:
        sql = "select max(fabe_uploaded_at) from fa_bankexplanation"
        cur = fa.env.get_cursor()
        cur.execute(sql)
        for row in cur:
            asof = str(row[0])[:19]      
        
    if item_type == 'transactions':
        if asof:
            params['updated_since'] = asof
        BankTransaction.download(fa, do_write, params)
        BankTransactionExplanation.download(fa, do_write, params)
    elif item_type == 'transaction_explanations':
        BankTransactionExplanation.download(fa, do_write, params)
    elif item_type == 'journals':
        JournalSet.download(fa, do_write, params)
        JournalEntry.download(fa, do_write, params)
    elif item_type == 'categories':
        Category.download(fa, do_write, params)
    elif item_type == 'accounts':
        BankAccount.download(fa, do_write, params)
    elif item_type == 'users':
        User.download(fa, do_write, params)
    elif item_type == 'all':
        Category.download(fa, do_write, params)
        BankAccount.download(fa, do_write, params)
        User.download(fa, do_write, params)
        JournalSet.download(fa, do_write, params)
        JournalEntry.download(fa, do_write, params)
        if asof:
            params['updated_since'] = asof

        BankTransaction.download(fa, do_write, params)
        BankTransactionExplanation.download(fa, do_write, params)
    elif item_type == 'variables':
        JournalSet.download(fa, do_write, params)
        JournalEntry.download(fa, do_write, params)
        if asof:
            params['updated_since'] = asof

        BankTransaction.download(fa, do_write, params)
        BankTransactionExplanation.download(fa, do_write, params)
    else:
        log.error("Unknown item type %s" % item_type)

    if not skip_db:
        sql = 'execute fa2all'
        fa.env.execute(sql)

def upload(fa, force=False):
    log.info('running upload')
    BankTransactionExplanation.upload_all(fa, force)
    JournalSet.upload_all(fa, force)


def create_upload_records(fa):
    log.info('running create_upload_records')
    sql = 'execute pcreate_upload_records'
    fa.env.execute(sql)
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="Primary command such as download or upload")
    parser.add_argument("-item_type", choices=['all', 'variables', 'journals', 'categories', 'accounts', 'users', 'transactions', 'transaction_explanations'], help="Item type to download/upload [transactions / journals / categories / accounts / users / all / variables [default: journals and transactions]]")
    parser.add_argument("-asof", type=str, action="store", help="Cutoff modification date for downloads; defaults to most recent download of given type")
    parser.add_argument("-readonly", action="store_true", help="Read data from FreeAgent, but do not write to database")
    parser.add_argument("-force", action="store_true", help="Read all transactions and explanations, not just those updated since the most recent update")
    parser.add_argument("-skip_db", action="store_true", help="Skip populating using fa2 procedures")
# 
    args = parser.parse_args()
#     


    fa = FreeAgent()
    fa.env.is_test = False
    fa.env.configure_logger(log)

    fa.read_parameters()
#     resp = fa.request('journal_sets/2176706', {})
#     print(resp)
#     log.info('Running' + ' '.join(sys.argv))
#     fa.read_parameters()
#    fa.refresh_access_token()
#    User.download(fa)


#    d = {}


#    BankTransactionExplanation.upload_all(fa)

    action = args.command
    if action == 'download':
        download(fa, args.item_type, args.asof, not args.readonly, args.force, args.skip_db)
    elif action == 'upload':
        upload(fa, args.force)
    elif action == 'all':
        download(fa, 'variables', args.asof, not args.readonly, args.force, args.skip_db)
        create_upload_records(fa)
        upload(fa, args.force)

    
# def main():
#     fa = FreeAgent()
# 
#     fa.get_transactions()
#     
#     conn = fa.get_connection()
#     cur = conn.cursor()
#     
#     for t in fa.bank_transactions:
#         t.write(cur)
#     for e in fa.bank_explanations:
#         e.write(cur)
#     conn.commit()


if __name__ == '__main__':
    main()