"""
A collection of Python utilities originally developed for the
"Python for Computational Science" book.
"""

import time, sys, os, re, getopt, math, threading, shutil, commands
from errorcheck import right_type
from scitools.StringFunction import StringFunction

def test_if_module_exists(modulename, msg='',
                          raise_exception=False, abort=True):
    """
    Test if modulename can be imported, and if not, write
    an error message and (optionally) raise an exception, continue or
    abort with sys.exit(1).
    """
    try:
        __import__(modulename)
        return True
    except ImportError:
        import debug
        message = 'Could not import module "%s" - it is '\
                  'not installed on your system. %s\n' % \
                  (modulename, msg)
        if raise_exception:
            if msg:
                print msg
                #print 'The problem arose in ', 
                debug.trace(frameno=-3)
            raise ImportError(message)
        else:
            if msg:
                print '\n', message
                #print 'The problem arose in ', 
                debug.trace(frameno=-3)
            if abort:
                sys.exit(1)
            else:
                return False
    except Exception, e:
        if msg:
            print message
            print 'Got an exception while trying to import %s:\n' % \
                modulename, e


def func_to_method(func, class_, method_name=None):
    """
    Add a function to a class class_ as method_name.
    If method_name is not given, func.__name__ becomes
    the name of the method.
    Borrowed from recipe 5.12 in the Python Cookbook.
    """
    setattr(class_, method_name or func.__name__, func)
    
    
def system(command, verbose=True, failure_handling='exit', fake=False):
    """
    User-friendly wrapping of the os.system/os.popen commands.
    Actually, the commands.getstatusoutput function is used on Unix
    systems, and the output from the system command is fetched.

    ================  ========================================================
    ================  ========================================================
    command           operating system command to be executed
    verbose           False: no output, True: print command prior to execution
    failure_handling  one of 'exit', 'warning', 'exception', or 'silent'
                      (in case of failure, the output from the command is 
                      always displayed)
    fake              if True, the command is printed but not run (for testing)
    return value      the same as commands.getstatusoutput, i.e., a boolean 
                      failure variable and the output from the command as a 
                      string object
    ================  ========================================================
    """
    if verbose:
        print 'Running operating system command\n   %s' % command
    if fake:
        return 0, 'testing "%s"' % command

    if sys.platform[:3] == 'win':
        result = os.popen(command)
        output = result.read()
        failure = result.close()
    else:
        # Unix/Linux/Mac:
        failure, output = commands.getstatusoutput(command)
    
    if failure:
        msg = 'Failure when running operating system command'\
              '\n  %s\nOutput:\n%s' % (command, output)
        if failure_handling == 'exit':
            print msg, '\nExecution aborted!'
            sys.exit(1)
        if failure_handling == 'warning':
            print 'Warning:', msg
        elif failure_handling == 'exception':
            raise OSError(msg)
        elif failure_handling == 'silent':
            pass
        else:
            raise ValueError('wrong value "%s" of failure_handling' % \
                             failure_handling)

    return failure, output


def read_cml(option, default=None, argv=sys.argv):
    """
    Search for option (e.g. '-p', '--plotfile') among the command-line
    arguments and return the associated value (the proceeding argument).
    If the option is not found, the default argument is returned
    as str(default) (to have a unified behavior in that everything returned
    from read_cml is a string).

    The call::
    
       str2obj(read_cml(option, default=...))

    will return a Python object (with the right type) corresponding to
    the value of the object (see the str2obj function).

    ================  ========================================================
    ================  ========================================================
    option            command-line option (str)
    default           default value associated with the option
    argv              list that is scanned for command-line arguments
    return value      the item in argv after the option, or default if option
                      is not found
    ================  ========================================================

    See the read_cml_func function for reading function expressions
    or function/instance names on the command line and returning
    callable objects.
    """
    try:
        index = argv.index(option)
        return argv[index+1]
    except ValueError:
        return str(default)
    except IndexError:
        raise IndexError('array of command-line arguments is too short; '\
                         'no value after %s option' % option)


    
def str2bool(s):
    """
    Turn a string s, holding some boolean value
    ('on', 'off', 'True', 'False', 'yes', 'no' - case insensitive)
    into boolean variable. s can also be a boolean. Example:
    
    >>> str2bool('OFF')
    False
    >>> str2bool('yes')
    True
    """
    if isinstance(s, str):
        true_values = ('on', 'true', 'yes')
        false_values = ('off', 'false', 'no')
        s2 = s.lower()  # make case insensitive comparison
        if s2 in true_values:
            return True
        elif s2 in false_values:
            return False
        else:
            raise ValueError('"%s" is not a boolean value %s' % \
                             (s, true_values+false_values))
    else:
        raise TypeError('%s %s cannot be converted to bool' % \
                        (s, type(s)))
    

def str2obj(s, globals_=None, locals_=None, debug=False):
    """
    Turn string s into the corresponding object. str2obj is mainly
    used to take a string from a GUI or the command line and
    create a Python object. For example:

    >>> s = str2obj('0.3')
    >>> print s, type(s)
    0.3 <type 'float'>
    >>> s = str2obj('(1,8)')
    >>> print s, type(s)
    (1, 8) <type 'tuple'>
    
    Method: eval(s) can normally do the job, but if s is meant to
    be turned into a string object, eval works only if s has explicit
    quotes:

    >>> eval('some string')
    Traceback (most recent call last):
    SyntaxError: unexpected EOF while parsing

    (eval tries to parse 'some string' as Python code.)
    Similarly, if s is a boolean word, say 'off' or 'yes',
    eval will not work.

    In this function we first try to see if s is a boolean value,
    using scitools.misc.str2bool. If this does is not successful,
    we try eval(s, globals_, locals_), and if it works, we return
    the resulting object. Otherwise, s is (most probably) a string,
    so we return s itself. The None value of locals_ and globals_
    implies using locals() and globals() in this function.

    Examples:

    >>> strings = ('0.3', '5', '[-1,2]', '-1+3j', 'dict(a=1,b=0,c=2)',
    ...            'some string', 'true', 'ON', 'no')
    >>> for s in strings:
    ...     obj = str2obj(s)
    ...     print '"%s" -> %s %s' % (s, obj, type(obj)
    ...
    "0.3" -> 0.3 <type 'float'>
    "5" -> 5 <type 'int'>
    "[-1,2]" -> [-1, 2] <type 'list'>
    "-1+3j" -> (-1+3j) <type 'complex'>
    "dict(a=1,b=0,=2)" ->  {'a': 1, 'c': 2, 'b': 0} <type 'dict'>
    "some string" -> some string <type 'str'>
    "true" -> True <type 'bool'>
    "ON" -> True <type 'bool'>
    "no" -> False <type 'bool'>
    >>>
    
    If the name of a user defined function, class or instance is
    sent to str2obj, the calling code must also send locals() and
    globals() dictionaries as extra arguments. Otherwise, str2obj
    will not know how to "eval" the string and produce the right
    object (user-defined types are unknown inside str2obj unless
    the calling code's globals and locals are provided).
    Here is an example:
    
    >>> def myf(x):
    ...     return 1+x
    ...
    >>> class A:
    ...     pass
    ...
    >>> a = A()
    >>>
    >>> s = str2obj('myf')
    >>> print s, type(s)   # now s is simply the string 'myf'
    myf <type 'str'>
    >>> # provide locals and globals such that we get the function myf:
    >>> s = str2obj('myf', locals(), globals())
    >>> print s, type(s)
    <function myf at 0xb70ffe2c> <type 'function'>
    >>> s = str2obj('a', locals(), globals())
    >>> print s, type(s)
    <__main__.A instance at 0xb70f6fcc> <type 'instance'>

    With debug=True, the function will print out the exception
    encountered when doing eval(s, globals_, locals_), and this may
    point out problems with, e.g., imports in the calling code
    (insufficient variables in globals_).

    Note: if the string argument is the name of a valid Python
    class (type), that class will be returned. For example,
    >>> str2obj('list')  # returns class list
    <type 'list'>
    """
    if globals_ is None:
        globals_ = globals()
    if locals_ is None:
        locals_ = locals()
    
    try:
        b = str2bool(s)
        return b
    except (ValueError, TypeError), e:
        # s is not a boolean value, try eval(s):
        try:
            b = eval(s, globals_, locals_)
            return b
        except Exception, e:
            if debug:
                print """
scitools.misc.str2obj:
Tried to do eval(s) with s="%s", and it resulted in an exception:
    %s
""" % (s, e)
            # eval(s) did not work, s is probably a string:
            return s


def str2type(value):
    """
    Return a function that can take a string and convert it to
    a Python object of the same type as value.
    
    This function is useful when turning input from GUIs or the
    command line into Python objects. Given a default value for the
    input (with the right object type), str2type will return the right
    conversion function.  (str2obj can do the thing, but will often
    return eval, which turns any string into a Python object - this is
    less safe than str2type, which never returns eval. That principle
    helps to detect wrong input.)

    Method: If value is bool, we use scitools.misc.str2bool, which
    is capable of converting strings like "on", "off","yes", "no",
    "true" and "false" to boolean values. Otherwise, we use
    type(value) as the conversion function. However, there is one
    problem with type(value) when value is an int while the user
    intended a general real number - in that case one may get
    wrong answers because of wrong (int) round off. Another problem
    concerns user-defined types. For those (which str2type knows
    nothing about) the str function is returned, implying that the
    conversion from a string to the right user-defined type cannot
    be done by the function returned from str2type.

    Examples:
    
    >>> f = str2type((1,4,3))
    >>> f.__name__
    'tuple'

    >>> f = str2type(MySpecialClass())
    >>> f.__name__
    'str'

    >>> f = str2type('some string')
    >>> f.__name__
    'str'

    >>> f = str2type(False)
    >>> f.__name__
    'str2bool'

    (Note that we could return eval if value is not a string or a boolean,
    but eval is never returned from this function to avoid conversion
    to an unintended type.)
    """
    if isinstance(value, bool):
        return str2bool
    elif isinstance(value, (basestring,int,float,complex,list,tuple,dict)):
        return type(value)
    else:
        # the type of value is probably defined in some unknown module
        return str
    

def interpret_as_callable_or_StringFunction(s, iv, globals_=None):
    """
    Return a callable object if s is the name of such an
    object, otherwise turn s to a StringFunction with
    iv as the name of the independent variable.
    Used by the read_cml function. The globals_ variable is set
    equal to the module's globals() by default (None).
    """
    if globals_ is None:
        globals_ = globals()
    try:
        evaled_s = eval(s, globals_)
        if callable(evaled_s):
            return evaled_s
        else:
            raise ValueError(
                'string "%s" could be evaluated, but is not callable' % s)
    except NameError, e:
        try:
            if isinstance(iv, str):  # single indep. variable?
                iv = [iv]
            func = StringFunction(s, independent_variables=iv,
                                  globals=globals_)
        except Exception, e:
            raise ValueError(
                '%s\n"%s" must be a function name, instance creation, \
                or string formula!' % (e, s))
        return func


def read_cml_func(option, default_func, iv='t', globals_=None):
    """
    Locate --option on the command line (sys.argv) and find
    the corresponding value (next sys.argv element).
    This value is supposed to specify a function.
    If --option is not found, the default_func (a given callable)
    argument is returned.

    The found value is interpreted as either the name of a callable
    (function or instance) or a string formula.  In both cases, a
    callable (user-define function, user-defined instance, or
    StringFunction object) is returned. For StringFunctions the iv
    argument specifies the name(s) of the independent variable(s).
    Parameters to StringFunction objects are not supported.  The
    globals_ argument are used for eval(callable_name) or when
    creating the  StringFunction object.

    Note that this function always returns a callable object,
    supposed to be a user-defined function.
    """
    if globals_ is None:
        globals_ = globals()
    if option in sys.argv:
        i = sys.argv.index(option)
        try:
            value = sys.argv[i+1]
        except IndexError:
            raise IndexError(
                'no value after option %s on the command line' \
                % option)
        value = interpret_as_callable_or_StringFunction\
                (value, iv, globals=globals_)
    else:
        value = default_func
    return value


def function_UI(functions, argv, verbose=True):
    """
    User interface for calling a collection of functions from the
    command line by writing the function name and its arguments.
    functions is a list of possible functions to be called. argv is
    sys.argv from the calling code.
    function_UI returns a command to be evaluated (function call)
    in the calling code.

    This function autogenerates a user interface to a module.
    Suppose a module has a set of functions::

      test_mymethod1(M, q, a, b)
      test_method2a(a1, a2, a3=0, doc=None)
      test_method2b()

    The following code automatically creates a user interface
    and executes calls to the functions above::

      from scitools.misc import function_UI
      function_names = [fname for fname in dir() if fname.startswith('test_')]
      function_UI(function_names, sys.argv)

    On the command line the user can now type::

      programname --help

    and automatically get a help string for each function, consisting
    of the function name, all its positional arguments and all its
    keyword arguments.

    Alternatively, writing just the function name::

      programname functionname

    prints a usage string if this function requires arguments, otherwise
    the function is just called.

    Finally, when arguments are supplied::

      programname functionname arg1 arg2 arg3 ...

    the function is called with the given arguments. Safe and easy use
    is ensured by always giving keyword arguments::

      programname functionname arg1=value1 arg2=value2 arg3=value3 ...

    """
    usage, doc = _function_args_doc(functions)

    def all_usage():
        for fname in sorted(usage):
            print fname, ' '.join(usage[fname])
            
    # call: function-name arg1 arg2 ...
    if len(argv) < 2:
        all_usage()
        sys.exit(1)

    function_names = [f.__name__ for f in functions]
    if len(argv) == 2 and argv[1] in function_names and usage[argv[1]]:
        fname = argv[1]
        print 'Usage:', fname, ' '.join(usage[fname])
        if doc[fname]:
            print '\nDocstring:\n', doc[fname]
        sys.exit(1)

    if len(argv) == 2 and argv[1].endswith('help'):
        all_usage()
        sys.exit(0)

    cmd = '%s(%s)' % (argv[1], ', '.join(argv[2:]))
    #if len(argv[2:]) == len(usage[fname]):
        # Correct no arguments (eh, can leave out keyword args...)
    if verbose:
        print 'Calling', cmd
    return cmd


def _function_args_doc(functions):
    """
    Create documentation of a list of functions.
    Return: usage dict (usage[funcname] = list of arguments, incl.
    default values), doc dict (doc[funcname] = docstring (or None)).
    Called by function_UI.
    """
    import inspect
    usage = {}
    doc = {}
    for f in functions:
        args = inspect.getargspec(f)
        if args.defaults is None:
            # Only positional arguments
            usage[f] = args.args
        else:
            # Keyword arguments too, build complete list
            usage[f.__name__] = args.args[:-len(args.defaults)] + \
                     ['%s=%s' % (a, d) for a, d in \
                      zip(args.args[-len(args.defaults):], args.defaults)]
        doc[f.__name__] = inspect.getdoc(f)
    return usage, doc


def before(string, character):   
    """Return part of string before character."""
    for i in range(len(string)):
        if c == character:
            return string[:i-1]

def after(string, character):
    """Return part of string after character."""
    for i in range(len(string)):
        if c == character:
            return string[i+1:]

def remove_multiple_items(somelist):
    """
    Given some list somelist, return a list where identical items
    are removed.
    """
    right_type(somelist, list)
    new = []
    helphash = {}
    for item in somelist:
        if not item in helphash:
            new.append(item)
            helphash[item] = 1
    return new

    
def find(func, rootdir, arg=None):
    """
    Traverse the directory tree rootdir and call func for each file.
    arg is a user-provided argument transferred to func(filename,arg).
    """
    files = os.listdir(rootdir)  # get all files in rootdir
    files.sort(lambda a,b: cmp(a.lower(),b.lower()))
    for file in files:
        fullpath = os.path.join(rootdir,file) # make complete path
        if os.path.islink(fullpath):
            pass # drop links...
        elif os.path.isdir(fullpath):
            find(func, fullpath, arg) # recurse into directory
        elif os.path.isfile(fullpath):
            func(fullpath, arg) # file is regular, apply func
        else:
            print 'find: cannot treat ', fullpath


def sorted_os_path_walk(root, func, arg):
    """
    Like os.path.walk, but directories and files are visited and
    listed in alphabetic order.
    """
    try:
        files = os.listdir(root)  # get all files in rootdir
    except os.error:
        return
    files.sort(lambda a,b: cmp(a.lower(), b.lower()))
    func(arg, root, files)
    for name in files:
        name = os.path.join(root, name)
        if os.path.isdir(name):
            sorted_os_path_walk(name, func, arg) # recurse into directory


def subst(patterns, replacements, filenames,
          pattern_matching_modifiers=0):
    """
    Replace a set of patterns by a set of replacement strings (regular
    expressions) in a series of files.
    The function essentially performs::

      for filename in filenames:
          file_string = open(filename, 'r').read()
          for pattern, replacement in zip(patterns, replacements):
              file_string = re.sub(pattern, replacement, file_string)

    A copy of the original file is taken, with extension `.old~`.

    ==========================  ======================================
    ==========================  ======================================
    patterns                    string or list of strings (regex)
    replacements                string or list of strings (regex)
    filenames                   string or list of strings
    pattern_matching_modifiers  re.DOTALL, re.MULTILINE, etc., same
                                syntax as for re.compile
    ==========================  ======================================
    """
    # if some arguments are strings, convert them to lists:
    if isinstance(patterns, basestring):
        patterns = [patterns]
    if isinstance(replacements, basestring):
        replacements = [replacements]
    if isinstance(filenames, basestring):
        filenames = [filenames]

    # pre-compile patterns:
    cpatterns = [re.compile(pattern, pattern_matching_modifiers) \
                 for pattern in patterns]
    modified_files = dict([(p,[]) for p in patterns])  # init
    messages = []   # for return info

    for filename in filenames:
        if not os.path.isfile(filename):
            raise IOError('%s is not a file!' % filename)
        f = open(filename, 'r');
        filestr = f.read()
        f.close()

        for pattern, cpattern, replacement in \
            zip(patterns, cpatterns, replacements):
            if cpattern.search(filestr):
                filestr = cpattern.sub(replacement, filestr)
                shutil.copy2(filename, filename + '.old~') # backup
                f = open(filename, 'w')
                f.write(filestr)
                f.close()
                modified_files[pattern].append(filename)

    # make a readable return string with substitution info:
    for pattern in sorted(modified_files):
        if modified_files[pattern]:
            replacement = replacements[patterns.index(pattern)]
            messages.append('%s replaced by %s in %s' % \
                                (pattern, replacement, 
                                 ', '.join(modified_files[pattern])))

    return ', '.join(messages) if messages else 'no substitutions'


# class Command has now been replaced by the standard functools.partial
# function in Python v2.5 and later:

class Command:
    """
    Alternative to lambda functions.

    This class should with Python version 2.5 and later be replaced
    by functools.partial.
    However, you cannot simply do a::

      Command = functools.partial

    to be backward compatible with your old programs that use Command,
    because Command and functools.partial supply the positional
    arguments in different manners: Command calls the underlying
    function with new arguments followed by the originally recorded
    arguments, while functools.partial does it the other way around
    (first original arguments, then new positional arguments).

    This Command class is kept for backward compatibility. New usage
    should employ functools.partial instead.
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        args = args + self.args
        self.kwargs.update(kwargs)
        self.func(*args, **self.kwargs)


def timer(func, args=[], kwargs={}, repetitions=10, comment=''):
    """
    Run a function func, with arguments given by the tuple
    args and keyword arguments given by the dictionary kwargs,
    a specified number of times (repetitions) and
    write out the elapsed time and the CPU time together.
    """
    t0 = time.time();  c0 = time.clock()
    for i in range(repetitions):
        func(*args, **kwargs)
    cpu_time = time.clock()-c0
    elapsed_time = time.time()-t0
    try:    # instance method?
        name = func.im_class.__name__ + '.' + func.__name__
    except: # ordinary function
        try:
            name = func.__name__
        except:
            name = ''
    print '%s %s (%d calls): elapsed=%g, CPU=%g' % \
          (comment, name, repetitions, elapsed_time, cpu_time)
    return cpu_time/float(repetitions)


def timer_system(command, comment=''):
    """
    Run an os.system(command) statement and measure the CPU time.
    With os.system, the CPU time is registered as the user and
    system time of child processes.

    Note: there might be some overhead in the timing compared to
    running time in the OS instead.
    """
    t0 = os.times()
    failure = os.system(command)
    t1 = os.times()
    # some programs return nonzero even when they work (grep, for inst.)
    if failure:
        print 'Note: os.system(%s) failed' % command, 'returned', failure
    cpu_time = t1[2]-t0[2] + t1[3]-t0[3]
    print '%s system command: "%s": elapsed=%g CPU=%g' % \
          (comment, command, t1[4]-t0[4], cpu_time)
    return cpu_time


def findprograms(programs, searchlibs=[], write_message=False):
    """
    Given a list of programs (programs), find the full path
    of each program and return a dictionary with the program
    name as key and the full path as value. The value is None
    if the program is not found.

    The program list can either be a list/tuple or a
    dictionary (in the latter case, the keys are the programs
    and the values are explanations of the programs).
    If write_message is true, the function writes a message
    if a program is not found. In that case, None is returned
    if not all programs are found.

    A single program can also be given as first argument. In that
    case, findprograms returns True or False according to whether
    the program is found or not.
    
    Example on usage::

      if findprograms('plotmtv'):
          os.system('plotmtv ...')

      # write a message if a program is not found:
      if findprograms(['plotmtv'], write_message=True):
          os.system('plotmtv ...')

      programs = ['gs', 'convert']
      path = findprograms(programs)
      if path['gs']:
          os.system('gs ...')
      if path['convert']:
          os.system('convert ...')

      programs = { 'gs' : 'Ghostscript: file format conversions',
                   'convert' : 'File format conversion from ImageMagick',
                 }
      if not findprograms(programs, write_message=True):
          print 'the mentioned programs need to be installed'
          sys.exit(1)
    """
    def program_exists(fullpath):
        if sys.platform.startswith('win'):
            # add .exe or .bat to program filename:
            if os.path.isfile(fullpath+'.exe') or \
               os.path.isfile(fullpath+'.bat'):
                return True
        elif os.name == 'posix': # Unix
            if os.path.isfile(fullpath):
                return True
        else:
            raise TypeError('platform %s/%s not supported' % \
                            (sys.platform, os.name))
        return False # otherwise
        
    path = os.environ['PATH']  # /usr/bin:/usr/local/bin:/usr/X11/bin
    paths = re.split(os.pathsep, path)
    fullpaths = {}
    if isinstance(programs, str):
        program = programs
        for dir in paths:
            if os.path.isdir(dir): # skip non-existing directories
                fullpath = os.path.join(dir,program)
                if program_exists(fullpath):
                    return True
        # else, not found:
        if write_message:
            print 'program %s not found' % programs
        return False

    elif isinstance(programs, (list,tuple)):
        # initialize with None:
        for program in programs:  fullpaths[program] = None
        for program in programs:
            for dir in paths:
                if os.path.isdir(dir): # skip non-existing directories
                    fullpath = os.path.join(dir,program)
                    if program_exists(fullpath):
                        fullpaths[program] = fullpath
                        break  # stop when the program is found

    elif isinstance(programs, dict):
        # initialize with None:
        for program in programs.keys():  fullpaths[program] = None
        for program in programs.keys():
            for dir in paths:
                if os.path.isdir(dir): # skip non-existing directories
                    fullpath = os.path.join(dir,program)
                    if program_exists(fullpath):
                        fullpaths[program] = fullpath
                        break
        
    if write_message:
        missing = False
        for program in fullpaths.keys():
            if not fullpaths[program]:
                if isinstance(program, dict):
                    print "program '%s' (%s) not found" % \
                          (program,programs[program])
                else:  # list or tuple
                    print 'program "%s" not found' % program
                missing = True
        if missing:
            return None
        
    return fullpaths


def pathsearch(programs=[], modules=[], where=0):
    """
    Given a list of programs (programs) and modules (modules),
    search for these programs and modules in the directories
    in the PATH and PYTHONPATH environment variables, respectively.
    Check that each directory has read and write access too.
    The function is useful for checking that PATH and PYTHONPATH
    are appropriately set in CGI scripts.
    """

    path = os.environ['PATH']  # /usr/bin:/usr/local/bin:/usr/X11/bin
    paths = re.split(os.pathsep, path)
    for program in programs:
        found = 0
        for dir in paths:
            if os.path.isdir(dir): # skip non-existing directories
                # check read and execute access in this directory:
                if not os.access(dir, os.R_OK | os.X_OK):
                    print dir, 'does not have read/execute access'
                    sys.exit(1)
                fullpath = os.path.join(dir,program)
                if os.path.isfile(fullpath):
                    found = 1
                    if where:
                        print program, 'found in', dir
                    break
        if not found:
            print "The program '%s' was not found" % program
            print 'PATH contains the directories\n','\n'.join(paths)

    path = os.environ['PYTHONPATH']
    paths = re.split(os.pathsep, path)
    for module in modules:
        found = 0
        for dir in paths:
            if os.path.isdir(dir): # skip non-existing directories
                # check read and execute access in this directory:
                if not os.access(dir, os.R_OK | os.X_OK):
                    print dir, 'does not have read/execute access'
                    sys.exit(1)
                fullpath = os.path.join(dir,module) + '.py'
                if os.path.isfile(fullpath):
                    found = 1
                    if where:
                        print module, 'found in', dir
                    break
        if not found:
            print "The module '%s' was not found" % module
            print 'PYTHONPATH contains the directories\n',\
            '\n'.join(paths)

def preprocess_all_files(rootdir, options=''):
    """
    Run preprocess on all files of the form basename.p.ext
    in the directory with root rootdir. The output of each
    preprocess run is directed to basename.ext.

    @param rootdir: root of directory tree to be processed.
    @param options: options (string) to preprocess program.
    @return: nested list of ((dir, basename.p.ext, basename.p), success))
    tuples. success is boolean and indicates if the preprocess command
    was a success (or not).
    """
    # first check that the user has the preprocess script:
    if not findprograms('preprocess'):
        raise SystemError('The preprocess program could not be found')
    
    def treat_a_dir(fileinfo, d, files):
        warning = """\
#############################################################################
# WARNING: This is an autogenerated file!! Do not edit this file!!
# Edit the original file %s (on which preprocess.py will be run)
#############################################################################
"""

        for f in files:
            path = os.path.join(d, f)
            if '.p.' in f and not '.svn' in f:
                basename_dotp, ext = os.path.splitext(f)
                basename, dotp = os.path.splitext(basename_dotp)
                outfilename = basename + ext
                outpath = os.path.join(d, outfilename)
                cmd = 'preprocess %s %s > %s' % (options, path, outpath)
                #print cmd
                failure, output = system(cmd, failure_handling='warning')
                fileinfo.append( ((d, f, outfilename), not failure))
                # add warning header:
                _warning = warning % f
                _f = open(outpath, 'r'); _str = _f.read(); _f.close()
                _lines = _str.split('\n')
                if _lines[0].startswith('#!'):
                    _lines.insert(1, _warning)
                else:
                    _lines.insert(0, _warning)
                _str = '\n'.join(_lines)
                _f = open(outpath, 'w'); _f.write(_str); _f.close()
                
    info = []
    os.path.walk(rootdir, treat_a_dir, info)
    return info


def pow_eff(a,b, powfunc=math.pow):
    """
    Returns a^b. Smart function that happened to be slower
    than a straight math.pow.
    """
    if b == 2:
        return a*a
    elif b == 3:
        return a*a
    elif b == 4:
        h = a*a
        return h*h
    elif b == 1:
        return a
    elif abs(b) < 1.0E-15:  # x^0 ?
        return 1.0
    elif a == 0.0:
        return 0.0
    else:
        # check if b is integer:
        bi = int(b)
        if bi == b:
            r = 1
            for i in range(bi):
                r *= a
            return r
        else:
            if a < 0:
                raise ValueError('pow(a,b) with a=%g<0')
            else:
                return powfunc(a, b)

    
def lines2paragraphs(lines):
    """
    Return a list of paragraphs from a list of lines
    (normally holding the lines in a file).
    """
    p = []             # list of paragraphs to be returned
    firstline = 0      # first line in a paragraph
    currentline = 0    # current line in the file
    lines.insert(len(lines), '\n') # needed to get the last paragraph
    for line in lines:
        # for each new blank line, join lines from firstline
        # to currentline to a string defining a new paragraph:
        #if re.search(r'^\s*$', line):  # blank line?
        if line.isspace():  # blank line?
            if currentline > firstline:
                p.append(''.join(lines[firstline:currentline+1]))
                #print 'paragraph from line',firstline,'to',currentline
            # new paragraph starts from the next line:
            firstline = currentline+1  
        currentline += 1
    return p


def oneline(infile, outfile):
    """
    Transform all paragraphs in infile (filename) to one-line strings
    and write the result to outfile (filename).
    """
    fi = open(infile, 'r')
    pp = lines2paragraphs(fi.readlines())
    fo = open(outfile, 'w')
    for p in pp:
        line = ' '.join(p.split('\n')) + '\n\n'
        fo.write(line)
    fi.close()
    fo.close()


def wrap(infile, outfile, linewidth=70):
    """
    Read infile (filename) and format the text such that each line is
    not longer than linewidth. Write result to outfile (filename).
    """
    fi = open(infile, 'r')
    fo = open(outfile, 'w')
    # the use of textwrap must be done paragraph by paragraph:
    from textwrap import wrap
    pp = lines2paragraphs(fi.readlines())
    for p in pp:
        #print 'paragraph:\n  "%s"' % p
        lines = wrap(p, linewidth)
        #print 'lines:\n', lines
        for line in lines:
            fo.write(line + '\n')
        fo.write('\n')
    fi.close()
    fo.close()

            
def fontscheme1(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('Helvetica', 13, 'normal')
    pulldown_font = ('Helvetica', 13, 'italic bold')
    scale_font    = ('Helvetica', 13, 'normal')
    root.option_add('*Font', default_font)
    root.option_add('*Menu*Font', pulldown_font)
    root.option_add('*Menubutton*Font', pulldown_font)
    root.option_add('*Scale.*Font', scale_font)

def fontscheme2(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('Helvetica', 10, 'normal')
    pulldown_font = ('Helvetica', 10, 'italic bold')
    scale_font    = ('Helvetica', 10, 'normal')
    root.option_add('*Font', default_font)
    root.option_add('*Menu*Font', pulldown_font)
    root.option_add('*Menubutton*Font', pulldown_font)
    root.option_add('*Scale.*Font', scale_font)

def fontscheme3(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('Fixed', 12, 'normal')
    root.option_add('*Font', default_font)

def fontscheme4(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('Fixed', 14, 'normal')
    root.option_add('*Font', default_font)

def fontscheme5(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('comic sans ms', 12, 'normal')
    root.option_add('*Font', default_font)

def fontscheme6(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('trebuchet ms', 12, 'normal bold')
    root.option_add('*Font', default_font)

def fontscheme7(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('verdana', 12, 'normal bold')
    root.option_add('*Font', default_font)

def fontscheme8(root):
    """Alternative font scheme for Tkinter-based widgets."""
    default_font  = ('verdana', 14, 'normal')
    root.option_add('*Font', default_font)




def movefiles(files, destdir, confirm=True, verbose=True, copy=True):
    """
    Move a set of files to a a destination directory tree,
    but let the original complete path be reflected in the
    destination tree.

    files         list of filenames
    destdir       root of destination directory tree
    confirm       let the user confirm movement of each file
    verbose       write out the original and new path of each file
    copy          True: copy, False: move

    The function is useful for backing up or temporarily moving
    files; the files are easily restored in their original
    locations since the original complete path is maintained in
    the destination directory tree.
    """
    if not os.path.isdir(destdir):
        os.mkdir(destdir)
    for file in files:
        perform_action = 'y'
        if confirm:
            print 'move %s to %s?' % (file, destdir)
            perform_action = sys.stdin.readline().strip()
        if perform_action in ('y', 'Y', 'yes', 'YES'):
            fullpath = os.path.abspath(file)
            # remove initial / (Unix) or C:\ (Windows):
            if sys.platform.startswith('win'):
                fullpath = fullpath[3:]
            else:  # Unix
                fullpath = fullpath[1:]
            newpath = os.path.join(destdir, fullpath)
            newdir = os.path.dirname(newpath)
            if not os.path.isdir(newdir): os.makedirs(newdir)
            shutil.copy2(file, newpath)
            if os.path.isfile(newpath):
                print 'fount',newpath
            s = 'copied'
            if not copy:  # pure move
                os.remove(file); s = 'moved'
            if verbose:
                print s, file, 'to', newpath

# backward compatibility:
from debug import debugregex, dump



class BackgroundCommand(threading.Thread):
    """
    Run a function call with assignment in the background.
    Useful for putting time-consuming calculations/graphics
    in the background in an interactive Python shell.

    >>> b=BG('f', g.gridloop, 'sin(x*y)-exp(-x*y)')
    >>> b.start()
    running gridloop('sin(x*y)-exp(-x*y)',) in a thread
    >>> # continue with other interactive tasks
    >>> b.finished
    True
    >>> b.f  # result of function call
    """

    def __init__(self, result='result', func=None, args=[], kwargs={}):
        self.result = result
        self.__dict__[self.result] = None
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.finished = False
        threading.Thread.__init__(self)
    def run(self):
        kw = [key+'='+self.kwargs[key] for key in self.kwargs]
        cmd = '%s=%s(%s,%s)' % (self.result, self.func.__name__,
                                ','.join(self.args), ','.join(kw))
        print 'running %s in a thread' % cmd
        self.__dict__[self.result] = self.func(*self.args,**self.kwargs)
        self.finished = True
        print cmd, 'finished'

BG = BackgroundCommand  # short form

class Download(threading.Thread):
    def __init__(self, url, filename):
        self.url = url;  self.filename = filename
        threading.Thread.__init__(self)
    def run(self):
        print 'Fetching', self.url
        urllib.urlretrieve(self.url, self.filename)
        print self.filename, 'is downloaded'

def hardware_info():
    """
    Note: This function is very simple - NumPy has a much more sophisticated
    module for extracting hardware and CPU information:
    numpy.distutils.cpuinfo. Here is an example on its usage::

      import numpy.distutils.cpuinfo, pprint
      pprint.pprint(numpy.distutils.cpuinfo.cpu.info)

    The present hardware_info function serves more as an illustration of
    how one can easily obtain the most basic hardware information using
    tools that comes with Python or are easily available from the system.

    ---------------------------------------------------------------------------
    
    Extract hardware information using Python's platform module
    and (if available) files such as /proc/cpuinfo.

    Return: dictionary with keys "uname", "identifier", "python version",
    "python build", and "cpuinfo".
    The "identifier" entry is a string that can be
    used in filenames (the string returned from platform.platform()).

    Recommended use::

      from scitools.misc import hardware_info
      import pprint; pprint.pprint(hardware_info())

    """
    result = {}
    
    # infofile on Linux machines:
    infofile = '/proc/cpuinfo'
    cpuinfo = {}
    if os.path.isfile(infofile):
        f = open(infofile, 'r')
        for line in f:
            try:
                name, value = [w.strip() for w in line.split(':')]
            except:
                continue
            if name == 'model name':
                cpuinfo['CPU type'] = value
            elif name == 'cache size':
                cpuinfo['cache size'] = value
            elif name == 'cpu MHz':
                cpuinfo['CPU speed'] = value + ' Hz'
            elif name == 'vendor_id':
                cpuinfo['vendor ID'] = value
        f.close()
    result['cpuinfo'] = cpuinfo
    
    # check out platform module:
    import platform
    result['uname'] = platform.uname()
    result['python version'] = platform.python_version()
    result['python build'] = platform.python_build()
    result['identifier'] = platform.platform()
    return result


def memusage(_proc_pid_stat = '/proc/%s/stat'%(os.getpid())):
    """
    Return virtual memory size in bytes of the running python.
    Copied from the SciPy package (scipy_test.testing.py).
    """
    try:
        f=open(_proc_pid_stat,'r')
        l = f.readline().split(' ')
        f.close()
        return int(l[22])
    except:
        return


def _test_memusage(narrays=100, m=1000):
    """
    Test the memusage function for monitoring the memory usage.
    Generate narrays arrays of size (m,m). Keep the array
    with probability 0.5, otherwise delete a previously
    allocated array.
    """
    import random, Numeric
    random.seed(12)
    refs = []
    for i in range(narrays):
        a = Numeric.zeros((m,m), Numeric.Float)
        if random.random() > 0.5:
            refs.append(a)
        elif len(refs) > 0:
            del refs[0]
        mu = memusage()/1000000.0
        print 'memory usage: %.2fMb' % mu


def isiterable(data):
    """Returns true of data is iterable, else False."""
    try:
        iter(data)
    except TypeError:
        return False
    return True

def flatten(nested_data):
    """
    Return a flattened iterator over nested_data.

    >>> nested_list = [[1,2],3,[4,5,6,[7,[8,9]]]]
    >>> flat = [e for e in flatten(nested_list)]
    >>> flat
    [1, 2, 3, 4, 5, 6, 7, 8, 9]

    (Minor adjustment of code by Goncalo Rodrigues, see
    http://aspn.activestate.com/ASPN/Mail/Message/python-tutor/2302348)
    """
    it = iter(nested_data)
    for e in it:
        # note: strings are bad because, when iterated they return 
        # strings, leading to an infinite loop
        if isiterable(e) and not isinstance(e, basestring):
            # recurse into iterators
            for f in flatten(e):
                yield f
        else:
            yield e

def primes(n):
    """
    Return the prime numbers <= n.
    Standard optimized sieve algorithm.
    """
    if n < 2:  return [1]
    if n == 2: return [1, 2]
    # do only odd numbers starting at 3
    s = range(3, n+1, 2)
    mroot = n**0.5
    half = len(s)
    i = 0
    m = 3
    while m <= mroot:
        if s[i]:
            j = (m*m-3)//2  # int div
            s[j] = 0
            while j < half:
                s[j] = 0
                j += m
        i = i+1
        m = 2*i+3
    return [1, 2] + [x for x in s if x]


def cmldict(argv, cmlargs=None, validity=0):
    """
    The cmldict function takes a dictionary cmlargs with default
    values for the command-line options and returns a modified form of
    this dictionary after the options given in the list argv are
    parsed and inserted. One will typically supply sys.argv[1:] as the
    argv argument. In case cmlargs is None, the dictionary is built
    from scratch inside the function.  The flag validity is false (0)
    if any option in argv can be inserted in cmlargs, otherwise the
    function will issue an error message if an option is not already
    present in cmlargs with a default value (notice that cmlargs=None
    and validity=1 is an incompatible setting).

    Example:
    cmlargs = {'p' : 0, 'file' : None, 'q' : 0, 'v' : 0}
    argv = "-p 2 --file out -q 0".split()
    p = cmldict(argv, cmlargs)

    p equals {'p' : 2, 'file' : out, 'q' : 0}
    """

    if not cmlargs:
        cmlargs = {}

    arg_counter = 0
    while arg_counter < len(argv):
        option = argv[arg_counter]
        if option[0] == '-':  option = option[1:]  # remove 1st hyphen
        else: 
            # not an option, proceed with next sys.argv entry
            arg_counter += 1; continue  
        if option[0] == '-':  option = option[1:]  # remove 2nd hyphen
        
        if not validity or option in cmlargs: 
            # next argv entry is the value:
            arg_counter += 1
            value = argv[arg_counter] 
            cmlargs[option] = value
        elif validity:
            raise ValueError("The option %s is not registered" % option)
        arg_counter += 1
    return cmlargs

def _cmldict_demo():
    args = "--m 9.1 --b 7 --c 0.1 -A 3.3".split()
    defaults = { 'm' : '1.8', 'func' : 'siny' }
    p = cmldict(args, defaults, 0)
    print p

    # shuffle values into other variables:
    m = p['m']
    b = p['b']
    # and so on (should have validity=1 to ensure that the
    # option keys are defined)
    
    # take action:
    for option in p.keys():
        if option == "m":
            print "option is m", p[option]
        elif option == "b":
            print "option is b", p[option]
        elif option == "c":
            print "option is c", p[option]
        elif option == "A":
            print "option is A", p[option]
        elif option == "func":
            print "option is func", p[option]

    args.append('--error'); args.append('yes')
    print "\nNow comes an exception (!)"
    p = cmldict(args, defaults, 1)

# used in StringFunction doc as an example:
def _test_function(x, c=0, a=1, b=2):
    if x > c:
        return a*(x-c) + b
    else:
        return -a*(x-c) + b

# -- tests ---
def f(a, b, max=1.2, min=2.2):  # some function
    print 'a=%g, b=%g, max=%g, min=%g' % (a,b,max,min)


class DoNothing(object):
    """
    Handy class for making other objects inactive.
    (DoNothing is a generic dispatcher, accepting anyting and
    doing nothing.)

    Whatever we do, we always get a DoNothing object, with which
    we can do whatever we want to, but nothing will happen.
    
    For example, say a plot function returns a plot object that
    is used widely in a code to create windows with visualizations
    on the screen, and you want to turn off all these visualizations:

    >>> from scitools.misc import DoNothing
    >>> plot = DoNothing('Plotting turned off')
    >>> viz = plot(u, wireframe=True, title='My plot')
    >>> type(viz)
    <class 'scitools.misc.DoNothing'>
    >>> viz.update(T)
    trying update but no action (DoNothing object)
    >>> q = viz.properties()
    trying properties but no action (DoNothing object)
    >>> type(q)
    <class 'scitools.misc.DoNothing'>
    """
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return DoNothing()
    def __repr__(self):
        return ''
    def __str__(self):
        return repr(self)
    def __getattribute__(self, name):
        print 'ignoring action "%s" (DoNothing object)' % name
        return DoNothing()
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration()
    
class Recorder:
    """
    This class is a wrapper of a module or instance which will
    record all actions done with the module/instance.

    >>> from scitools.misc import Recorder
    >>> from scitools.std import plt, plot, linspace
    >>> x = linspace(-1,1,10)
    >>> y1 = x**2
    >>> y2 = x**3
    >>> plt._g = Recorder(plt._g)  # make the plot object record itself
    >>> plot(x, y1, 'r-',
    ...      x, y2, 'b-',
    ...      title='A test')
    [<scitools.easyviz.common.Line object at 0x1749c50>, <scitools.easyviz.common.Line object at 0x1749bd0>]
    >>> # look at what we have done with the plt._g object
    >>> plt._g.replay()
    reset()
    __call__('unset multiplot',)
    __call__('set datafile missing "nan"',)
    __call__('set key right top',)
    __call__('set title "A test"',)
    __call__('unset logscale x',)
    __call__('unset logscale y',)
    __call__('set autoscale',)
    __call__('set xrange[*:*]',)
    __call__('set yrange[*:*]',)
    __call__('set zrange[*:*]',)
    __call__('set size noratio',)
    __call__('set size nosquare',)
    __call__('set yrange [] noreverse',)
    __call__('set hidden3d',)
    __call__('unset colorbox',)
    __call__('set cbrange [*:*]',)
    __call__('set palette model RGB defined (0 "blue", 3 "cyan", 4 "green", 5 "yellow", 8 "red", 10 "black")',)
    __call__('unset view',)
    __call__('set view map',)
    __call__('set xtics',)
    __call__('set ytics',)
    __call__('set ztics',)
    __call__('set border 1+2+4+8+16 linetype -1 linewidth .4',)
    __call__('unset xlabel',)
    __call__('unset ylabel',)
    __call__('unset zlabel',)
    __call__('set border 4095 linetype -1 linewidth .4',)
    __call__('unset grid',)
    plot(<Gnuplot.PlotItems._FIFOFileItem instance at 0x174d998>,)
    replot(<Gnuplot.PlotItems._FIFOFileItem instance at 0x174db90>,)
    
    """
    def __init__(self, obj):
        self.obj = obj
        self.recorder = []

    def __getattr__(self, name):
        return _RecordHelper(self.obj, name, self.recorder)

    def replay(self):
        for name, args, kwargs in self.recorder:
            s = name + '('
            if args:
                s += str(args)[1:-1]
            if kwargs:
                s += ', ' + ', '.join(['%s=%s' % (key, kwargs[key]) for key in kwargs])
            s += ')'
            print s
        
class _RecordHelper:
    def __init__(self, obj, name, recorder):
        self.obj, self.name, self.recorder = obj, name, recorder

    def __call__(self, *args, **kwargs):
        self.recorder.append((self.name, args, kwargs))
        if hasattr(self.obj, self.name):
            return getattr(self.obj, self.name)(*args, **kwargs)
        else:
            raise AttributeError('%s has no attribute %s', (self.obj, name))

        

def fix_latex_command_regex(pattern, application='match'):
    """
    Given a pattern for a regular expression match or substitution,
    the function checks for problematic patterns commonly
    encountered when working with LaTeX texts, namely commands
    starting with a backslash. 

    For a pattern to be matched or substituted, and extra backslash is
    always needed (either a special regex construction like \w leads
    to wrong match, or \c leads to wrong substitution since \ just
    escapes c so only the c is replaced, leaving an undesired
    backslash). For the replacement pattern in a substitutions, specified
    by the application='replacement' argument, a backslash
    before any of the characters abfgnrtv must be preceeded by an
    additional backslash.

    The application variable equals 'match' if pattern is used for
    a match and 'replacement' if pattern defines a replacement
    regex in a re.sub command.

    Caveats: let pattern just contain LaTeX commands, not combination
    of commands and other regular expressions (\s, \d, etc.) as the
    latter will end up with an extra undesired backslash.

    Here are examples on failures:

    >>> re.sub(r'\begin\{equation\}', r'\[', r'\begin{equation}')
    '\\begin{equation}'
    >>> # match of mbox, not \mbox, and wrong output:
    >>> re.sub(r'\mbox\{(.+?)\}', r'\fbox{\g<1>}', r'\mbox{not}')
    '\\\x0cbox{not}'

    Here are examples on using this function:

    >>> from scitools.misc import fix_latex_command_regex as fix
    >>> pattern = fix(r'\begin\{equation\}', application='match')
    >>> re.sub(pattern, r'\[', r'\begin{equation}')
    '\\['
    >>> pattern = fix(r'\mbox\{(.+?)\}', application='match')
    >>> replacement = fix(r'\fbox{\g<1>}', application='replacement')
    >>> re.sub(pattern, replacement, r'\mbox{not}')
    '\\fbox{not}'

    Avoid mixing LaTeX commands and ordinary regular expression
    commands, e.g.:

    >>> pattern = fix(r'\mbox\{(\d+)\}', application='match')
    >>> pattern
    '\\\\mbox\\{(\\\\d+)\\}'
    >>> re.sub(pattern, replacement, r'\mbox{987}')
    '\\mbox{987}'  # no substitution, no match
    """
    import string
    problematic_letters = string.ascii_letters if application == 'match' \
                          else 'abfgnrtv'

    for letter in problematic_letters:
        problematic_pattern = '\\' + letter

        if letter == 'g' and application == 'replacement':
            # no extra \ for \g<...> in pattern
            if r'\g<' in pattern:
                continue

        ok_pattern = '\\\\' + letter
        if problematic_pattern in pattern and not ok_pattern in pattern:
            pattern = pattern.replace(problematic_pattern, ok_pattern)
    return pattern



if __name__ == '__main__':
    try:
        task = sys.argv[1]
    except:
        task = ''

    if task == 'debugregex':
        r = r'<(.*?)>'
        s = '<r1>is a tag</r1> and <s1>s1</s1> is too.'
        print debugregex(r,s)
        print debugregex(r'(\d+\.\d*)','a= 51.243 and b =1.45')

