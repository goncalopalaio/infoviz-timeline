# infoviz-timeline

Tool that enables events to be rendered on the screen for debugging/logging purposes.

The idea is to have a socket server listening for external events and render them in some ways as they appear.

Desired features:

- Have an internal windowing system like imgui so the tool has the ability to render into different windows at the same time.

- Control the timeline and and be able to go back in the events. Since the events are incremental all previous events would have to be rendered again, but would it would be possible to stop in a certain point in time.

- Control the time that each message takes to be processed. This would be useful to have the events being rendered in slow motion.

Desired features related to each type of message:

- Render a specific image that is on disk after a particular socket message is received.

- Render shapes, like a circle into an existing image after a particular socket message is received.

- Render text into a log window after a particular socket message is received.

- Render matrix values after a particular socket message is received.

This is meant to have one way communication right now (client -> server) but maybe it could be used to propagate values back to the client at some point.
