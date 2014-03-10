Getting Started
===============

To get started defining experiments, there several steps:

#. Determine what parts of your app you'd like to optimize
#. Setup a storage engine (currently only json, though mongo+zodb are in the roadmap)
#. Instantiate Bandits for all your experiments (you can have as many as you like, several experiments
   can run at once in a single app.)
#. Assign arms to your bandits that represent your experimental states
#. Attach the BanditMiddleware to your Flask app.

This guide will take you through each step.  The example case we'll be working with is included in the source under the
'example' folder if you'd like to try running the finished product.

Determining what to test
------------------------

The first task at hand requires a little planning.  What are some of the things in your app you've always
been curious about changing, but never had empirical data to back up potential modifications?  Bandits are best
suited to cases where changes can be "slipped in" without the user noticing, but since the state assigned to a user
will be persisted to their client, you can also change things like UI.

For our example case, we'll be changing the label text and color of a button in our app to see if either change increases
user interaction with the feature.  We'll be representing these states as two separate experiements (so a user will get separate
assignments for color and text) but you could conceviably make them one experiment by utilizing a tuple or sequence.  More on that later!

Setting up your storage backend
--------------------------------

HTTP itself is stateless, but bandits need to persist their increments between requests.  In order to accomplish this, there is a 
bandit storage interface that can be implemented to save all the experiments for an application down to memory, database, etc.

At present, the only core implementation of this interface saves the bandits down to a JSON file at the path you specify, but this should
work for most purposes.  For 1.0 release, implementations using MongoDB and ZODB are planned.

Storage engines are attached using flask configuration directives.

Let's start setting up our bandit file storage::

    app.config['MAB_STORAGE_ENGINE'] = 'JSONBanditStorage'
    app.config['MAB_STORAGE_OPTS'] = ('./example/bandit_storage.json',) 

This storage instance will be passed into our bandit middleware and all values that need to be persisted will be handled under the hood.

The storage opts are just arguments to be passed to the storage instance constructor (in this case, just the path to a flat file to store the information.)

Create bandits and assigning arms
---------------------------------

The next step is to create a bandit for each experiment we want to test.

There are several different bandit implemenations included, but for the purposes of this example we'll be using an :mod:`flask_mab.bandits.EpsilonGreedyBandit`,
an algorithm which aggressively assigns the present winner according to a fixed constant value, `epsilon`

Expanding upon our previous example, here are our bandits alongside our storage engine::

    from flask.ext.mab.storage import JSONBanditStorage
    from flask.ext.mab.bandits import EpsilonGreedyBandit

    color_bandit = EpsilonGreedyBandit(0.2)
    color_bandit.add_arm("green","#00FF00")
    color_bandit.add_arm("red","#FF0000")
    color_bandit.add_arm("blue","#0000FF")

    txt_bandit = EpsilonGreedyBandit(0.5)
    txt_bandit.add_arm("casual","Hey dude, wanna buy me?")
    txt_bandit.add_arm("neutral","Add to cart")
    txt_bandit.add_arm("formal","Good day sir... care to purchase?")

Here we have two bandits, one of which will randomize %20 of the time on the color of the button, the other %50 of the time on the text.  The colors and
test blurbs are considered our "arms" in the bandit parlance.  An epsilon greedy bandit splits states between random selection and deterministically 
selecting the "winner", so as users click more, thereby sending reward signals, one combination of these two states will start to win out.

This code could easily be refactored using a function or generator, but for now, we'll include the full boilerplate.  If you have a lot of experiments, consider 
defining a function to be more convenient.

Attaching the middleware
------------------------

The main :mod:`flask_mab.__init__.BanditMiddleware` is where all the magic happens.  Attaching it to our app, assigning it some bandits, and sending it pull and reward 
signals is all that's necessary to get the test going.

Expanding on our example, we'll define a simple flask app with some basic routes for rendering the interface.  These routes will also understand how to reward the right
arms and update the bandits so the state of the experiment starts adjusting in realtime.

Again, boilerplate here could be easily cut down, but here is a rough example::

    from flask import Flask,render_template
    from flask.ext.mab import BanditMiddleware

    app = Flask('test_app')
    mab = BanditMiddleware() 
    mab.init_app(app)
    app.add_bandit('color_btn',color_bandit) #our bandits from previous code block
    app.add_bandit('txt_btn',txt_bandit)

    @app.route("/")
    def home():
        """Render the btn"""
        return render_template("ui.html")

    @app.route("/btnclick")
    def home():
        """Button was clicked!"""
        return render_template("btnclick.html")

Now our app understands that it should be tracking two experiments and persisting their values to a file.  "Arms" that get selected for every 
user will be persisted to cookies.  However, we still need to make the system understand what endpoints use which experiments.  In our example case,
the "/" route is going to render the button, and so both states will need to be assigned there.  The "/btnclick" endpoint, alternatively, is where our 
`reward` is determined, the theoretical "payoff" that state won us.  In this case, its a boolean, assigning a 1 if the button gets clicked.  So how are these
two signals sent to the middleware?  There are decorators much like the `route` decorator that easily registers these actions.

Using the decorators
++++++++++++++++++++

Setting up the MAB feedback cycle is easily negotiated by endpoint::

    @app.route("/")
    @mab.choose_arm("color_btn")
    @mab.choose_arm("txt_btn")
    def home():
        """Render the btn using values from the bandit"""
        return render_template("ui.html",btn_color=home.color_btn,btn_text=home.txt_btn)

    @app.route("/btnclick")
    @mab.reward_endpt("color_btn",1.0)
    @mab.reward_endpt("txt_btn",1.0)
    def reward(color_btn, txt_btn):
        """Button was clicked!"""
        return render_template("btnclick.html")

Using these decorators, our middleware knows that the it should suggest some values for both our experiments at the root endpoint.  When decorating with `choose_arm`, we identify the bandit/experiment we need a value
assignment for. 

It should be stressed that things like colors are probably best stored in CSS, but for this example we'll pass the values right into jinja.  You could consider setting up a 
dedicated endpoint for experiments with static styles like this, one that could parse and render your CSS.  The rough idea here is to leave what the bandit actually affects up to you.

On the other side of the process, our "/btnclick" endpoint now knows that whatever "arms" assigned to this user worked out well, because the user clicked it.  The 
:meth:`flask_mab.__init__.BanditMiddleware.reward_endpt` decorator knows to look in our user's cookie for the values that were assigned to her and give them some props.  We're using
booleans here, but you could pass any amount of reward in the event that some states in your experiment are better than others (you could for example weight your experiments differently.)

That's it!  This user's feedback will be persisted by the middleware and used to adjust the content for future users.  Over time, this pattern will start converging to a winner.
Your app will get optimized on these two experimental features for free!

This toy example is implemented and included alongside the source code in the example directory.
