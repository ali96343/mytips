from gluon.sql import SQLDB

class MetaData(object):
    def __init__(self,db): self.db=db

class _String(object):
    def __init__(self):
        self.p=dict(type='string',length=64)
    def __call__(self,*a,**b):
        other=_String()
        if a: other.p['length']=int(a[0])
        return other
String=_String()
Unicode=_String()  ### no distinction in web2py

class _Text(object):
    def __init__(self):
        self.p=dict(type='text')
    def __call__(self,*a,**b):
        other=_Text()
        return other
Text=_Text()

class _Binary(object):
    def __init__(self):
        self.p=dict(type='blob')
    def __call__(self,*a,**b):
        other=_Binary()
        return other
Binary=_Binary()

class _Integer(object):
    def __init__(self):
        self.p=dict(type='integer')
Integer=_Integer()

class _Float(object):
    def __init__(self):
        self.p=dict(type='double')
Float=_Float()
Numeric=_Float()

class _Datetime(object):
    def __init__(self):
        self.p=dict(type='datetime')
Datetime=_Datetime()

class _Time(object):
    def __init__(self):
        self.p=dict(type='time')
Time=_Time()

class _Boolean(object):
    def __init__(self):
        self.p=dict(type='boolean')
Boolean=_Boolean()

class _ForeignKey(object):
    def __init__(self):
        self.p=dict(type='reference unkown')
    def __call__(self,*a):
        other=_ForeignKey()
        other.p['type']='reference %s' % a[0].split('.')[0]
        return other
ForeignKey=_ForeignKey()

FLOAT=Numeric
TEXT=String
DECIMAL=Numeric
INT=INTEGER=Integer
TIMESTAMP=Datetime
CLOB=Text
VARCHAR=String
BLOB=Binary
BOOLEAN=Boolean

def Column(name,typecol,*a,**b):
    return lambda db: db.Field(name,**typecol.p)

def Table(tablename,metadata,*a,**b):
    db=metadata.db
    migrate=b.get('migrate',True)
    fields=[f(db) for f in a if type(f)==type(lambda:None)]
    id=[f for f in fields if f.name=='id']
    if not id: SyntaxError, 'no id field'
    fields=[f for f in fields if not f.name=='id']
    return db.define_table(tablename,migrate=migrate,*fields)

def test_sqlalchemy_model():
    db=SQLDB()
    metadata=MetaData(db)
 
    users = Table('users', metadata,
       Column('id', Integer),
       Column('name', String(40)),
       Column('age', Integer),
       Column('password', String),
       Column('blob1',Binary),
    )

    groups = Table('groups', metadata,
       Column('id', Integer),
       Column('name', String(40)),
       Column('owner', ForeignKey('users.id')),
    )

    print users.fields
    print groups.fields

if __name__=='__main__': test_sqlalchemy_model()
