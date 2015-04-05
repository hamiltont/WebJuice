
# NOTE: This is pre-alpha

This is a fancy way of saying it doesn't do anything useful yet, and probably won't run on your setup

Requirements and Installation
-----------------------------

Requires: MySQL, Python 2.7.9

**Installation**

* Clone this repo, cd into new directory
* Install dependencies
* * `virtualenv env`
* * `source env/bin/activate`
* * `pip install -r requirements.txt`

**Launch (OS X only currently)**

* Turn on Docker VM and launch MySQL Container
* * `boot2docker start`
* * `$(boot2docker shellinit)`
* * `docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=toor -d mysql`
* * `boot2docker ip`
* Run software
* * `source env/bin/activate`
* * `supervisord`

**Interfaces**

Note that there are hyperlinks on the `About` page to important services

* [Flask](http://127.0.0.1:5000/)
* [Flower](http://localhost:5555/)
* [RabbitMQ Management Interface](http://192.168.59.103:15672/) (use `$ boot2docker ip`)

You cannot access `boot2docker` exposed ports using `localhost`, you
have to use the IP address presented by `boot2docker ip`

* MySQL - `http://$(boot2docker ip):3306`
* RabbitMQ - `http://$(boot2docker ip):5672`

**Halting**

While normally using `Ctrl-C` with supervisord works fine, occasionally
you may need to kill orphaned python processes using `killall -9 python`

Why Python, why Flask?
----------------------

Ok, fair question for a project that benchmarks web frameworks...

I chose Python for consistency with the existing toolset, full stop.
I'll debate language preference as much as the next programmer, but 
for this case I wanted consistency to encourage maintainability and 
future contributions. I had never written any web applications using 
Python before, so I made the best framework judgement I could. 
Flask didn't require many new concepts for me (I suspect it won't for 
most people---yay future contributions), and has a nice balance of 
flexibility vs simplicity. 
A big seller for me was also Flask's clean supports JADE templates
(via `pyjade`)--I like the cleanness of JADE and how its space-dependant 
style is similar to Python. 

For open source especially, I tend to value having
working code available at a minimum level of performance--this 
codebase is my attempt to get a continuous system off the ground.
I won't be surprised or sad at all if someone rewrites the entire 
app one day (in fact, it would be a huge success!). Happy hacking ;-)

