
# NOTE: This is pre-alpha

This is a fancy way of saying it doesn't do anything useful yet, and probably won't run on your setup

Requirements and Installation
-----------------------------

[![Inline docs](http://inch-ci.org/github/hamiltont/WebJuice.svg?branch=master)](http://inch-ci.org/github/hamiltont/WebJuice)
[![Code Climate](https://codeclimate.com/github/hamiltont/WebJuice.png)](https://codeclimate.com/github/hamiltont/WebJuice)

Requires: Python 2.7.9, Docker, Redis (Only in Production)

**Setup**

```bash
# Get source code
git clone https://github.com/hamiltont/WebJuice.git
cd WebJuice

# Install dependencies
virtualenv env
source env/bin/activate
pip install -r requirements.txt

# If running in developer mode, use docker to setup a 
# container running Redis
python start_redis.py
```

**Launch**

Simply put, launching is as easy as calling `foreman start`. This will spin 
up Flask, Flower, and Celery. 

However, before you can launch you should set environment variables so we 
can connect to your Docker host. Using 
[Docker Machine](https://docs.docker.com/machine/) is easy, it will 
automatically setup Docker in a range of environments (OS X, 
Windows, Linux, Amazon, Digital Ocean, Rackspace, etc) and setup these 
environment variables

Docker environment variables: 
* Required   : `DOCKER_HOST`
* Required   : `DOCKER_HOST_IP`
* Recommended: `DOCKER_TLS_VERIFY`
* Recommended: `DOCKER_CERT_PATH`

After you setup a Docker provider using `docker-machine`, use

```bash
$ eval "$(docker-machine env)"
$ export DOCKER_HOST=`docker-machine ip`
```

**Management Interfaces**

There are hyperlinks on the `About` page to important services, including Flask, Flower, and the RabbitMQ Management Interface

**Halting**

Using `Ctrl-C` with foreman works fine 95% of the time. Occasionally
you may need to kill orphaned python processes using `killall -9 python`

Why Python, why Flask?
----------------------

Ok, fair question for a project that benchmarks web frameworks...

I chose Python for consistency with the FrameworkBenchmarks project, full stop.
I'll debate language preference as much as the next developer, but 
in this case I wanted language consistency to encourage maintainability and 
future contributions. 

Why Flask? I hadn't used any Python web frameworks before this project,  
so I made the best judgement I could. 
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


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/hamiltont/webjuice/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

