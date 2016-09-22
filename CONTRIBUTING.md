# Contributing to icgc-get #

## Getting Started ##

Software is made better by people like you. If you wish to contribute code to the project we can definitely help you get started. Before continuing please read through this document to ensure that you
understand the expectations set fourth for anyone wishing to make this project better.

* Github is our project source home so please ensure you have a registered Github account before continuing.
* We use a variant of the [Gitflow](https://datasift.github.io/gitflow/index.html)  workflow for our version control management. This means that your
contributions will be managed using [git branching](http://nvie.com/posts/a-successful-git-branching-model/) and Pull Requests.
* Our main stable branch is ```develop``` so please clone and perform your Pull Requests (PRs) towards this branch.

## Coding Conventions ##

Follow this: https://www.python.org/dev/peps/pep-0008/

### Strings ###

#### Single quotes outside, double quotes inside
**YES:**
```python
some_string = 'this is a string'
another_string = 'Oh hey, look at this string="foobar"'
```

**NO:**
```python
foo = "aaaa"
bar = "My string: 'baz'"
```


#### Format strings with the format function
**YES:**
```python
'Look at my pretty string: {}'.format(pretty_string)
```

**NO:**
```python
'I like TypeErrors like this one: %s` % unknown_type
```


### Exceptions ###

#### Never silently suppress exceptions
**YES:**
```python
try:
    # Some operation
    ...
except SomeError as e:
    logging.exception("Operation foo had an exception")
    
```

**NO:**
```python
try:
    # Some operation
    ...
except SomeError as e:
    continue
```

#### Platform Independence 

#### Use platform independent abstractions when possible
**YES:**
```python
open(os.devnull, 'w')
```

**NO:**
```python
open('/dev/null', 'w')
```