from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfile
from tkinter.filedialog import askopenfile
import traceback
import terragen_rpc as tg

gui = Tk()
gui.title("tg_rename_1_1_1_nodes.py")
gui.geometry("320x140")
gui.config(bg="#89B2B9")

gui.rowconfigure(0,weight=2)
gui.rowconfigure(1,weight=1)
gui.columnconfigure(0,weight=1)
gui.columnconfigure(1,weight=1)
gui.columnconfigure(2,weight=1)

frame0 = LabelFrame(gui,text="Display results in order of ...",relief=FLAT,bg="#B8DBD0",padx=4)
frame1 = LabelFrame(gui,bg="#89B2B9",relief=FLAT)
frame0.grid(row=0,column=0,padx=10,pady=10,sticky="WENS")
frame1.grid(row=1,column=0,padx=4,pady=0)

# global variables
search_pattern = "_1"
all_names_in_project = []
new_names = []
suggested_name = ""
list_of_tuples = []
button_choice = IntVar()
button_choice.set(1)

def get_nodes_in_project(): # gets the root nodes and passes them to the in_node function
    try:
        file_path = tg.project_filepath()
        if file_path == "":
            file_path = "untitled project"

        project = tg.root()
        names, ids = get_nodes_in_node(project)
        
        return names, ids, file_path
    
    except ConnectionError as e:
        popup_warning("Terragen RPC connection error",str(e))
        return [],[],"Terragen RPC connection error"
    except TimeoutError as e:
        popup_warning("Terragen RPC timeout error",str(e))
        return [],[],"Terragen RPC timeout error"
    except tg.ReplyError as e:
        popup_warning("Terragen RPC reply error",str(e))
        return [],[],"Terragen RPC reply error"
    except tg.ApiError:
        popup_warning("Terragen RPC API error",traceback.format_exc())
        return [],[],"Terragen RPC API error"

def get_nodes_in_node(in_node_id):
    global search_pattern
    node_names = []
    node_ids = []    
    try:
        all_children_ids = in_node_id.children()
        for child in all_children_ids:
            child_name = child.name()
            node_names.append(child_name)
            if child_name[-2:] == search_pattern:
                child_name_id = (child_name, child) # child name and node id
                node_ids.append(child_name_id)
            deeper_names, deeper_ids = get_nodes_in_node(child)
            node_names.extend(deeper_names)
            node_ids.extend(deeper_ids)
        return node_names,node_ids
    
    except ConnectionError as e:
        popup_warning("Terragen RPC connection error",str(e))
        return [],[]
    except TimeoutError as e:
        popup_warning("Terragen RPC timeout error",str(e))
        return [],[]
    except tg.ReplyError as e:
        popup_warning("Terragen RPC reply error",str(e))
        return [],[]
    except tg.ApiError:
        popup_warning("Terragen RPC API error",traceback.format_exc())
        return [],[]

def names_with_numeric_suffix(truncate_name):
    does_name_already_exist = 1 # assume exists
    starting_number = int(truncate_name[-2:])
    increment_by = 0
    while does_name_already_exist >= 0:
        increment_by = increment_by + 1
        next_number = starting_number + increment_by
        suggested_name = truncate_name[:-2] + str(next_number).zfill(2)
        name_exist = does_name_exist_in_project(suggested_name)
        if name_exist == 0: # means suggested name is not in use
            does_name_already_exist = -1
    return(suggested_name)

def names_with_alphabetic_suffix(truncate_name):
    does_name_already_exist = 1 # assume exists
    increment_by = 0
    while does_name_already_exist >= 0:
        increment_by = increment_by + 1
        suggested_name = truncate_name + " " + str(increment_by).zfill(2)
        name_exist = does_name_exist_in_project(suggested_name)
        if name_exist == 0:
            does_name_already_exist = -1
    return (suggested_name)

def does_name_exist_in_project(name): # this function checks to see if the suggested name already exists in the list of all names and list of new names
    global all_names_in_project
    global new_names
    exist = 1 # assume exists
    for i in all_names_in_project:
        if name  == i:
            return(exist)
    if len(new_names) > 0: # first time through, won't be anything in the list
        for i in new_names:
            if name == i:
                return(exist)
    exist = 0 # name doesn't exist yet
    return (exist)

def popup_save_results_to_disk(summary):
    response = messagebox.askyesno(title="tg_rename_1_1_1_nodes.py",message=summary)
    if response == True:
        write_results_to_disk(summary)
    if response == False:
        pass

def write_results_to_disk(summary):
    my_filetypes = [("Text document","*.txt"),("All files","*.*")]
    file = asksaveasfile(filetypes= my_filetypes, defaultextension=my_filetypes)
    file.write(summary[:-30]) # don't need to write the ending question to disk, just the data.
    file.close()

def popup_warning(message_type,message_description):
    messagebox.showwarning(title=message_type, message = message_description)

def update_project(new_names): # argument is a list of tuples. elements are new name and node path and old node name
    try:
        for item in new_names:
            try:
                node_id = item[1]
                old_name = node_id.name()
                node_id.set_param('name',item[0])
            except AttributeError as e:  # this occurred when a node was renamed that also had child nodes in its internal node network. Should no longer occur as using node ids not paths
                print ("FAILED on ",item," ",str(e)) # not handled well
    except ConnectionError as e:
        popup_warning("Terragen RPC connection error",str(e))
    except TimeoutError as e:
        popup_warning("Terragen RPC timeout error",str(e))
    except tg.ReplyError as e:
        popup_warning("Terragen RPC reply error",str(e))
    except tg.ApiError:
        popup_warning("Terragen RPC API error",traceback.format_exc())

def summary_of_changes(list_of_tuples,project_file_path):
    user_choice = button_choice.get()    
    compare_results_string = project_file_path + "\n\n"
    sorted_list_of_tuples = list_of_tuples

    if user_choice == 2:
        sorted_list_of_tuples = sorted(list_of_tuples,key=lambda x: x[2])
    elif user_choice == 3:
        sorted_list_of_tuples = sorted(list_of_tuples,key=lambda x: x[2],reverse=True)
    
    for item in sorted_list_of_tuples:
        compare_results_string = compare_results_string + str(item[2]) + "  to  " + str(item[0] + "\n")

    compare_results_string = compare_results_string + "\n" + str(len(list_of_tuples)) + " nodes renamed. \n\n"
    compare_results_string = compare_results_string + "SAVE REPORT SUMMARY TO DISK? \n"

    return compare_results_string

def main():
    global all_names_in_project
    global list_of_tuples
    all_names_in_project.clear()
    list_of_tuples.clear()
    all_names_in_project, nodes_to_replace,project_file_path = get_nodes_in_project() # step 1 - get two lists. Names of all nodes. List of tuples (name, path) (name, node_ids) and file path
    if len(nodes_to_replace) > 0:
        for node in nodes_to_replace: # step 2 - remove search pattern from name
            truncate_name = node[0]
            while (truncate_name[-len(search_pattern):] == search_pattern):
                    truncate_name = truncate_name[:-len(search_pattern)]

            if truncate_name[-2:].isdigit():
                    new_node_name = names_with_numeric_suffix(truncate_name)
                    new_names.append(new_node_name)
            else:        
                new_node_name = names_with_alphabetic_suffix(truncate_name)
                new_names.append(new_node_name)
            
            temp_tuple = (new_node_name, node[1], node[0]) # new node name, node id, old node name
            list_of_tuples.append(temp_tuple)

        # update project via rpc
        update_project(list_of_tuples)
    else:
        list_of_tuples.clear() # so that when the script is run again without closing the previous contents are purged

    # summary report
    summary = summary_of_changes(list_of_tuples,project_file_path)
    popup_save_results_to_disk(summary)

r1 = Radiobutton(frame0,text = 'Project order',variable=button_choice, value=1,bg="#B8DBD0")
r1.grid(row=1,column=0,padx=4,pady=8)
r2 = Radiobutton(frame0,text = 'A - Z order',variable=button_choice, value=2,bg="#B8DBD0")
r2.grid(row=1,column=1,padx=4,pady=8)
r3 = Radiobutton(frame0,text = 'Z - A order',variable=button_choice, value=3,bg="#B8DBD0")
r3.grid(row=1,column=2,padx=4,pady=8)

go_button = Button(frame1,text="Rename nodes",command=main,bg="#EEEE7A")
go_button.grid(row=0,column=0,padx=4,pady=8)

gui.mainloop()