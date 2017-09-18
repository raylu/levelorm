# levelorm

a python 3.6+ ORM for [leveldb](http://leveldb.org) using [plyvel](https://plyvel.readthedocs.io/)

## basic usage

```python
import levelorm
from levelorm.fields import String, Boolean
import plyvel

db = plyvel.DB('demodb', create_if_missing=True)
DBBaseModel = levelorm.db_base_model(db)

class Animal(DBBaseModel):
    prefix = 'animal'
    name = String(key=True)
    onomatopoeia = String()
    shouts = Boolean()

    def say(self):
        output = self.onomatopoeia
        if self.shouts:
            output = output.upper()
        return output

Animal('cow', 'moo', shouts=True).save()
cow = Animal.get('cow')
print(cow.name, 'says', cow.say())

print(list(Animal.iter()))
```
```
cow says MOO
[Animal(name='cow', onomatopoeia='moo', shouts=True)]
```
