# notbook

An argument that [Jupyter Notebooks](https://jupyter.org/) are conceptually flawed just as spreadsheets are - 
**the (python) world needs a successor.**

To try and convince you of that I've built a quick demo of on alternative. 
TL;DR [here's](https://samuelcolvin.github.io/notbook/) an example of the kind of document that's generated.

But before you look at that, I should convince you notebooks have fundamental problems...

---

# Quiz:

## Question: What's the common flaw between Jupyter Notebooks and Excel?

### Answer 1: They both don't work with version control

True, that's very annoying. Both `.xlsx` and `.ipynb` show as blobs, it's impossible to clearly see what's changed 
in either between versions. 

**But it's not the real problem, try again.**

### Answer 2: The logic they contain can't be directly used in production

Another good try. It's virtually impossible to have clearly visible logic in either a notebook or an excel sheet
which can also be used in production. You end up copying the logic out, rewriting it and adding it to your production
stack. 

Problems come when you want to modify the logic and share it with someone again, now you have two (somewhat different)
implementations to keep track of and keep identical.

**But still not the fundamental common problem, try again...**

### Answer 3: Bugs are common since they're both easy to partially update

Remember `ctrl + alt + shift + F9` in Excel? Go for coffee and wait for it to update, and hope nothing crashes, 
search through all you sheets to see if anything has gone wrong. 
Notebooks are no better - sections don't automatically 
update when an earlier section is modified, so you end up running "Run All Cells" the whole time. 
But even that's not the whole problem, because notebooks reuse a single python process, you can have more subtle 
bugs: declare a function in one cell, then use it in the next - all works well, now delete the function from the 
first cell, but the function object still exists in globals, so the notebook continues to work. 
Now you send that sheet to someone else and of course everything fails!

But that's not all: both excel and notebooks don't make it obvious when an error has happened, you could have an 
exception in a cell that's offscreen (or a sheet you're not looking at) and you wouldn't be aware of it.

**That's a big problem, but really it's just an implementation mistake, not the root problem, keep trying...**

### Answer 4: Bugs are common since they don't provide an easy way of writing unit tests

True, just as you can't reuse logic in a production environment, you can't easily access logic outside the main
document to write unit tests.

**Mad, but still not THE problem, keep trying...**

### Answer 5: Neither let me write logic in my IDE/editor of choice

So annoying, anyone who writes code for more than a few hours a month becomes very at-home in their editor of choice.
Having to leave it to use either excel or notebooks is really painful, plus both lack many of the advanced features
of a modern IDE.

**Still not the answer I'm looking for, have another try...**

### Answer 6: Neither give me a viewer-friendly way of displaying their results

Excel is awful at displaying complex results, particularly with a narrative. Notebooks are better at describing
a narrative, but they're still ugly - you have to show lots of code that the casual reader doesn't care about 
(like imports and utility functions), there's also no really pretty way of displaying a notebook that I know of.

**Still not the right answer, have one more guess...**

### The real answer: Logic, results and even input data are combined in one horrid blob

YES! That the fundamental problem, and has led to many very serious (heisen)bugs. I personally have fallen into
this bear pit more than once.

Three conceptually very different things:
* input data (sometimes, with both it's theoretically possible to read input data from external sources)
* logic to calculate results (and parameters for those calculations)
* the results

Are stored in the same file.

Imagine if python automatically appended the output of a script to that script every time you ran it!

Of course this didn't seem like a big problems when spreadsheets were conceived in the 60s (the word "spreadsheet" or
"spread-sheet" [comes from](https://en.wikipedia.org/wiki/Spreadsheet#Paper_spreadsheets) 
two facing pieces of paper used as a leger). 
They were designed as just a clever table, just as you had the inputs and output on the same piece of paper when 
you did manual accounts on lined paper; it seemed sensible to keep everything in one file when building the 
computerised equivalent. 
But why on earth did anyone think this was still a good idea when inventing notebooks?

You would never think of storing your customer data in the same file as the logic to generate their invoices 
(unless you're still using excel) - so why would you store the results of your 
machine learning model along side its definition?

**This is the fundamental problem with both excel and notebooks, it's the root cause of many of the issues described 
above and the reason most experience develops eschew both.**

---

# My proposed alternative:

(Here my MVP is called "notbook", but if anyone actually wants to use it, it should be renamed to avoid confusion
with Jupyter Notebooks.)

A program that executes a python script, and renders an HTML document with:
* sections of the code, smartly rendered
* the output of print commands shown beneath the associated print statement
* comments rendered as markdown for the body of the document, again inserted in the right place in the document
* rich objects e.g. plots and table rendered properly in the document
* (not yet built) allow HTML inputs (text inputs, number inputs, range slides etc.) in the HTML to change the 
  inputs to calculations
* (not yet built) link to imported python modules which can be rendered recursively as more hybrid documents or just 
  as highlighted python

That document can be built either using:

### notbook build ...

`notbook build my-logic.py` - where the HTML document is built once and the process exists, if execution raises
an exception, no document is built and the processes exits with code `1`.

To view the document generated with the `notbook build demo-script.py` see
**[samuelcolvin.github.io/notbook/](https://samuelcolvin.github.io/notbook/)**.

### notbook watch ...

`notbook watch my-logic.py` - where the file is watched and a web-server is started showing the document,
when the file changes the HTML document is updated and the page automatically updates giving almost instant feedback.

Watch mode in action:

![Notbook watch mode screencast](https://github.com/samuelcolvin/notbook/blob/master/screen.gif "Notbook watch mode screencast")

### The script is just python

The python script(s) containing all logic:
 * only contain valid python syntax
 * be executable via the standard `python` CLI
 * be importable into other code and be able to import other code 

This might not sound like much (it's basically just another static site generator which works on python files, not
markdown etc.), but I think it could dramatically improve the workflow for data scientists and anyone python-literate
currently using notebooks or excel.

### Advantages

* It fixes all the issues described in the "quiz" above
* **it's simpler** - because the process here is dramatically simpler than notebooks, the source code is much smaller. 
  Therefore extending it, fixing bugs and customising usage should be much easier.

### Disadvantages

* perhaps in some scenarios slightly slower than running code in an existing python process 
  (this is currently exacerbated by [this issue with bokeh](https://github.com/bokeh/bokeh/issues/10007))
* probably some other stuff I can't think of right now
* seriously I can't see the downsides of this relative to notebooks, please create and issue if you think differently

### Further enhancements

There's much more this could do:
* the two things marked as "not yet built" above
* rendering tables from pandas and similar
* currently there's basic support for [bokeh](https://docs.bokeh.org/en/latest/index.html) plots but other 
  plotting libraries should be supported
* stage caching so slow steps in calculations could be cached between executions
* richer printing: currently [`devtools.debug`](https://github.com/samuelcolvin/python-devtools) is used to
  print complex objects (e.g. not `str`, `int`, `float`), this should be replaced with an interactive tree-view
  like chrome
* server based mode - instead of running the python script locally and showing it on localhost, the python source
  is posted to a server which runs the script and renders the results at some URL for the develop (or anyone else
  with permissions) to view
* ability to "import" or otherwise reference content in markdown files, rather than always using comments
* a "zip mode" and renderer of "zip mode": zips all the assets need to render a document, you can then send that binary
  file to someone to view, they can display the zipped document without having to mess about with the command line to
  get the document extracted and ready to view
