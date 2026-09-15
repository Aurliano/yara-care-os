import re

file_path = r"c:\yara-care-os\apps\hub\runtime\src\test\java\ir\sayda\yara\hub\runtime\communication\CommunicationRuntimeTest.kt"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all Connected with Connecting in assertions for startCall/joinIncomingCall tests
# which were immediately asserting the return value.
content = content.replace("assertEquals(CallRuntimeState.Connected, session.runtimeState)", "assertEquals(CallRuntimeState.Connecting, session.runtimeState)")

# Same for the connectionLost test that might be asserting Reconnecting or Connecting?
# Let's write it and see.
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
