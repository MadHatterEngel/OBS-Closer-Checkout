import re

with open('reviewer_app.py', 'r') as f:
    content = f.read()

# Update the delete logic to use ID instead of station/task
# old: supabase.table('station_tasks').delete().eq('station', station).eq('task', task).execute()
# new: supabase.table('station_tasks').delete().eq('id', task_dict['id']).execute()

# Wait, the exact string is:
#                             supabase.table('station_tasks').delete().eq('station', station).eq('task', task).execute()
old_del = "                            supabase.table('station_tasks').delete().eq('station', station).eq('task', task).execute()"
new_del = "                            supabase.table('station_tasks').delete().eq('id', task_dict['id']).execute()"
content = content.replace(old_del, new_del)

with open('reviewer_app.py', 'w') as f:
    f.write(content)
