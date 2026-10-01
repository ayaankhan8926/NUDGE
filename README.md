\# NUDGE



\## Autonomous work, with a human leash.



NUDGE is a supervised agent that turns one plain-English goal into a controlled sequence of actions across connected work tools.



Instead of blindly executing actions, NUDGE follows:



\*\*PLAN → ACT → OBSERVE → ASK\*\*



It can inspect workspace data, identify what needs attention, prepare actions, execute approved actions, observe the result, and replan when the situation changes.



The key principle is simple:



> \*\*NUDGE can act autonomously, but consequential actions remain under human control.\*\*



\---



\## 1. The Problem



Modern work is spread across multiple applications.



A simple task such as:



> "Check overdue invoices, find which clients have not replied, follow up with them, and update the invoice sheet."



can require a person to manually:



1\. Check an invoice sheet.

2\. Search email.

3\. Compare clients and responses.

4\. Decide who needs a follow-up.

5\. Draft an email.

6\. Send the email.

7\. Update the invoice record.

8\. Verify that the actions actually happened.



Traditional automation can execute predefined workflows, but real-world tasks often require observation, reasoning, and decisions.



NUDGE is designed around this gap.



\---



\# 2. What NUDGE Does



NUDGE receives a single natural-language goal.



It then:



1\. Understands the goal.

2\. Creates an execution plan.

3\. Inspects the connected workspace.

4\. Analyzes the available information.

5\. Identifies the next useful action.

6\. Passes the action through a programmatic risk gate.

7\. Executes safe actions automatically.

8\. Pauses before consequential actions.

9\. Waits for human approval, rejection, or editing.

10\. Executes the approved action.

11\. Observes the result.

12\. Replans based on what actually happened.



This creates a controlled agent loop:



```text

&#x20;               ┌──────────────┐

&#x20;               │    GOAL      │

&#x20;               └──────┬───────┘

&#x20;                      │

&#x20;                      ▼

&#x20;               ┌──────────────┐

&#x20;               │     PLAN     │

&#x20;               └──────┬───────┘

&#x20;                      │

&#x20;                      ▼

&#x20;               ┌──────────────┐

&#x20;               │     ACT      │

&#x20;               └──────┬───────┘

&#x20;                      │

&#x20;                      ▼

&#x20;               ┌──────────────┐

&#x20;               │   OBSERVE    │

&#x20;               └──────┬───────┘

&#x20;                      │

&#x20;                      ▼

&#x20;               ┌──────────────┐

&#x20;               │    REPLAN    │

&#x20;               └──────┬───────┘

&#x20;                      │

&#x20;             ┌────────┴────────┐

&#x20;             │                 │

&#x20;             ▼                 ▼

&#x20;         COMPLETE        HUMAN REVIEW

