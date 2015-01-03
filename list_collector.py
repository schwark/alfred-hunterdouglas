import string
import hunterdouglas
from alfred import Feedback

TYPES = ("rooms", "shades", "scenes")
COMMANDS = ("up", "down")
VERBS = {"rooms": "Roll", "scenes": "Run", "shades": "Roll"}

def execute_command(command):
    #print "command is {command}".format(command=command)
    global TYPES, COMMANDS, VERBS
    parts = command.split('.')
    kind = parts[0]
    internal_id = parts[1]
    command = parts[2]

    if not kind in TYPES:
        return None

    if(kind == "scenes"):
        hunterdouglas.set_scene(internal_id)
    elif(kind == "shades"):
        hunterdouglas.set_shade(internal_id, command)
    else:
        hunterdouglas.set_room(internal_id, command)
    return

def choose_command(current, latest):
    # if current is None, then no contest
    if not current:
        return (latest, current)
    # if one of them is a word command, that wins
    if current in COMMANDS:
        return (current, latest)
    if latest in COMMANDS:
        return (latest, current)
    # if both are digits, choose larger number
    if current.isdigit() and latest.isdigit():
        if int(current) > int(latest):
            return (current, latest)
        else:
            return (latest, current)
    # if one of them is a two digit number, that wins
    if current.isdigit() and len(current) > 1:
        return (current, latest)
    if latest.isdigit() and len(latest) > 1:
        return (latest, current)
    return (current, latest)

def list_collector(query="",kind="scenes"):
    global TYPES, COMMANDS, VERBS
    #print("list_collector: query is {query}").format(query=query)

    feedback_list = []
    feedback = Feedback()

    if not kind in TYPES:
        return feedback

    args = string.split(query, " ")    
    executable = False
    
    term = ''
    command = None
    for currentArg in args:
        if currentArg in COMMANDS or currentArg.isdigit():
            command, currentArg = choose_command(command, currentArg)
            executable = True
        if currentArg != command and currentArg:
            term += ' {ca}'.format(ca=currentArg)
    term = term.strip()

    if command and command.isdigit():
        if(int(command) < 0):
            command = '0'
        elif (int(command) > 100):
            command = '100'
            
    results = hunterdouglas.find_by_name(kind, term)
    for result in results:
        label = result["name"]
        internal_id = result["id"]

        if len(term) > 0:
            if not term.lower() in label.lower():
                continue

        arg = "{kind}.{internal_id}.{command}".format(kind=kind, internal_id=internal_id, command=command)
        verb = VERBS[kind]

        executable=True
        if kind != "scenes" and not command:
            executable = False
            title = "{verb} {target}".format(verb=verb, target=label)
        elif kind != "scenes" and command in COMMANDS:
            title = "{verb} {command} {target}".format(verb=verb, command=command, target=label)
        elif kind != "scenes" and command.isdigit():
            title = "{verb} {target} to {command}% up".format(verb=verb, command=command, target=label)
        elif kind == "scenes":
            title = "{verb} {target}".format(verb=verb, target=label)
            
        if title:
            feedback_list.append({'title':title, 'subtitle':label, 'arg':arg, 'valid':executable, 'autocomplete':' {l} '.format(l=label)})    

    feedback_list = sorted(feedback_list, key=lambda k:k['subtitle'])
    for item in feedback_list:
        feedback.addItem(title=item['title'], subtitle=item['subtitle'], arg=item['arg'], valid=item['valid'], autocomplete=item['autocomplete'])
    
    return feedback


def main():
    print list_collector('bedroom','shades')

if __name__ == "__main__":
    main()

