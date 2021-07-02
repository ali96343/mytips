from gluon.sql import SQLDB
from gluon.validators import *

isAlphaNumeric=IS_ALPHANUMERIC()
isAlphaNumericURL=IS_URL()
isSlug=IS_MATCH(r'^[-\w]+$')
isLowerCase=IS_LOWER()
isUpperCase=IS_UPPER()
isValidIPAddress4=IS_MATCH(r'^\d{1,3}(\.\d{1,3}){3}$')
isNotEmpty=IS_NOT_EMPTY()
isOnlyDigits=IS_MATCH(r'^\d*$')
isNotOnlyDigits=IS_MATCH(r'^[^\d]*$')
isInteger=IS_INT_IN_RANGE(-10**10,10**10)
isOnlyLetters=IS_MATCH(r'^[a-zA-Z]*$')
isValidANSIDate=IS_DATE()
isValidANSITime=IS_TIME()
isValidEmail=IS_EMAIL()
isValidPhone=IS_MATCH(r'^\+?\d{0,2}\-?\d{3}\-?\d{3}\-?\d{4}$')
isValidURL=IS_URL()

#Undefined validators

#isValidImage
#isValidImageURL
#isValidQuicktimeVideoURL
#isValidHTML
#isWellFormedXml
#isWellFormedXmlFragment
#isExistingURL
#isValidUSState
#hasNoProfanities

class DjangoField:
   def __init__(self,*a,**b):
       self.a=a
       self.b=b
       self.validators=[]
       self.attributes={}
       if a: self.attributes['label']=str(a[0])
       if b.get('null',False)==False: self.attributes['notnull']=True
       if b.get('blank',False)==False:
           self.attributes['required']=True
           self.validators.append(IS_NOT_EMPTY())
       if b.get('default',None): self.attributes['default']=b['default']
       if b.get('unique',False): self.attributes['unique']=True
       if b.get('max_length',None):
           length=self.attributes['length']=b['max_length']
           self.validators.append(IS_LENGTH(length))
       if b.get('verbose_name',None): self.attributes['label']=b['verbose_name']
       for v in b.get('validator_list',[]): self.validators.append(v)
       if b.get('choices',None)!=None: 
           self.validators=IS_IN_SET([x for x,y in b['choices']],[y for x,y in b['choices']])
       self.attributes['requires']=self.validators

class CharField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db): return dict(type='string',**self.attributes)

class TextField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db): return dict(type='text',**self.attributes)

class IntegerField(DjangoField):
   def __init__(self,*a,**b):
       DjangoField.__init__(self,*a,**b) 
       self.attributes['requires'].append(IS_INT_IN_RANGE(-10**10,10**10))
   def serial(self,name,db): return dict(type='integer',**self.attributes)

class FloatField(DjangoField):
   def __init__(self,*a,**b):
       DjangoField.__init__(self,*a,**b) 
       self.attributes['requires'].append(IS_FLOAT_IN_RANGE(-10**10,10**10))
   def serial(self,name,db): return dict(type='double',**self.attributes)

class BooleanField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db): return dict(type='boolean',**self.attributes)

class DateField(DjangoField):
   def __init__(self,*a,**b):
       DjangoField.__init__(self,*a,**b) 
       self.attributes['requires'].append(IS_DATE())
   def serial(self,name,db): return dict(type='date',**self.attributes)

class DateTimeField(DjangoField):
   def __init__(self,*a,**b):
       DjangoField.__init__(self,*a,**b) 
       self.attributes['requires'].append(IS_DATETIME())
   def serial(self,name,db): return dict(type='datetime',**self.attributes)

class TimeField(DjangoField):
   def __init__(self,*a,**b):
       DjangoField.__init__(self,*a,**b) 
       self.attributes['requires'].append(IS_TIME())
   def serial(self,name,db): return dict(type='time',**self.attributes)

class SlugField(DjangoField):
   def __init__(self,*a,**b):
       DjangoField.__init__(self,*a,**b) 
       self.attributes['requires'].append(IS_APHANUMERIC())
   def serial(self,name,db): return dict(type='string',**self.attributes)

class FileField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db): return dict(type='upload',**self.attributes)

class ImageField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db): return dict(type='upload',**self.attributes)

class EmailField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db):
       self.attributes['requires'].append(IS_EMAIL())
       return dict(type='string',**self.attributes)

class URLField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db):
       self.attributes['requires'].append(IS_URL())
       return dict(type='string',**self.attributes)
   
class ForeignKey(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db):
       other=str(self.a[0])
       self.attributes['requires']=IS_IN_DB(db,db[other].id,db[other][db[other].fields[1]])
       return dict(type='reference '+other,**self.attributes)

class ManyToManyField(DjangoField):
   def __init__(self,*a,**b): DjangoField.__init__(self,*a,**b) 
   def serial(self,name,db,migrate):
       other=str(self.a[0])
       db_name=self.b.get('db_name','%s__%s' % (name,other))
       db.define_table(db_name,db.Field(name,db[name]),db.Field(other,db[other]),migrate=migrate)
       self.attributes['requires']=IS_IN_DB(db,'%s.%s' % (db_name,name), '%(id)s')
       return dict(type='reference '+db_name,**self.attributes)

def DjangoModelFactory(db,migrate=True):
    class DjangoModelMetaClass(type):        
        def __new__(cls,name,bases,attrs):
            obj = type.__new__(cls,name,bases,attrs)
            if name!='DjangoModel':
                db=obj._db
                fields=[db.Field(key,**value.serial(name,db)) for key,value in attrs.items() if hasattr(value,'serial') and not isinstance(value,ManyToManyField)]                
                table=db.define_table(name,migrate=migrate,*fields)
                fields=[value.serial(name,db,migrate) for key,value in attrs.items() if not name in db.tables and isinstance(value,ManyToManyField)]
                return table
            return obj
    class DjangoModel(object):
        __metaclass__=DjangoModelMetaClass
        _db=db
        def __init__(self,**values):
            table=self.TABLE
            for key in table.fields: self.__setattr__(key,table[key].default)
            for key,value in values.items():
                if key=='id' or not key in table.fields: raise SyntaxError, "invalid field"
                self.__setattr__(key,value)
        def __setattr__(self,key,value):
            if not key in self.TABLE.fields: raise SyntaxError, "invalid field"
        def save(self):
            table=self.TABLE
            fields={}
            for key in table.fields:
                if key=='id': continue
                fields[key]=self.__getattribute__(key)
            table.insert(**fields)
    return DjangoModel


def test_django_model():
    db=SQLDB()
    Model=DjangoModelFactory(db,migrate=False)

    class Poll(Model):
        name=CharField('Name',max_length=32,null=True)
        description=TextField(null=True,blank=True)
        created_on=DateField(null=True,blank=True)

    class Choice(Model):
        poll=ForeignKey(Poll)
        value=CharField(validator_list=[isLowerCase],choices=((1,1),(2,2)))

    class Person(Model):
        name=CharField('Full Name',max_length=64,null=True)
        choices=ManyToManyField(Choice)

    Poll.insert(name='text')
    for row in db(Poll.id>0).select(): print row
    db.commit()

    print Poll.created_on.requires
    print Choice.value.requires

if __name__=='__main__': test_django_model()
