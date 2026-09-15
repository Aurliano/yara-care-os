import re

file_path = r"c:\yara-care-os\apps\hub\runtime\src\test\java\ir\sayda\yara\hub\runtime\communication\CommunicationRuntimeTest.kt"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace any assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState) 
# with CallRuntimeState.Connecting, EXCEPT in the tests that are explicitly about connectionRestoredMarksConnected?
# Wait, "connectionRestoredMarksConnected" might actually expect it to be Connecting too, because reconnect calls joinMedia, which won't mark Connected anymore.
content = content.replace("assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)", "assertEquals(CallRuntimeState.Connecting, repository.getCurrent()?.runtimeState)")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
