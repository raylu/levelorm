# levelorm

a python 3.6+ ORM for [leveldb](http://leveldb.org) using [plyvel](https://plyvel.readthedocs.io/)

## basic usage

```python
import plyvel

import levelorm
from levelorm.fields import String, Boolean

db = plyvel.DB('demodb', create_if_missing=True)
DBBaseModel = levelorm.db_base_model(db)

class Animal(DBBaseModel):
    prefix = 'animal'
    name = String(key=True)
    otomotopeia = String()
    shouts = Boolean()

    def say(self):
        output = self.otomotopeia
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
[Animal(name='cow', otomotopeia='moo', shouts=True)]
```