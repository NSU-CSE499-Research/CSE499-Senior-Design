# Turn the demo into a three-person capstone

The ZIP contains an implemented demonstration, not proof of research novelty. The strongest next step is to turn “prediction + counterfactual replay” into a narrow, measurable learning question.

**Candidate question:** Does a same-state alternate trajectory help learners correct an inertia or rendezvous misconception more effectively than an ordinary trajectory replay?

## Three work packages

| Member | Main ownership | Concrete outputs |
| --- | --- | --- |
| 1 — Learning and research | Literature review, misconception definitions, explanation wording, evaluation design | Comparison matrix, pre/post questions, tutor decision table, study protocol, analysis plan |
| 2 — Simulation and validation | Force model, numerical integration, mission design, replay reproducibility | Physics specification, convergence results, trace schema, validated alternate branches, numerical regression checks |
| 3 — Interface and delivery | Responsive interface, input/accessibility, learner flow, export and packaging | Browser-tested UI, demo video, presentation, installation guide, usability findings |

All three should review the same interface contract: mission ID, initial state, prediction, actions, observed trace, alternate trace, and learning outcome. Hold one integration review each week using an end-to-end flight.

## Suggested next six weeks

| Week | Shared milestone | Evidence to retain |
| --- | --- | --- |
| 1 | Review this prototype, confirm scope, and run it on the actual presentation laptops/phones | Screenshots captured on those devices, issue list, model assumptions, role assignments |
| 2 | Complete a focused prior-art comparison and choose one learning concept | Source-backed comparison matrix and a precise contribution statement |
| 3 | Make replay reproducible from exported control events, with versioned model parameters | Import-and-replay demonstration and error thresholds |
| 4 | Pilot the interface with a small convenience sample, after any required institutional review | Usability notes, ambiguous questions, corrected task wording |
| 5 | Compare ordinary replay with alternate-trajectory replay using the approved study design | De-identified results, timing, completion, and pre/post concept scores |
| 6 | Analyze results, document limits, and rehearse the capstone demonstration | Final report, poster/slides, video, release ZIP, and reproducibility appendix |

Sample size and claims should follow the study design; do not treat this schedule as justification for a particular statistical conclusion. If there is no user study, present a validated engineering prototype and describe learning effectiveness as future work.

## High-value engineering extensions

1. Record every control event with its simulation timestamp, then import and rerun the exact sequence.
2. Let a learner choose a branch point and replace a single burn, while preserving the state at that point.
3. Show synchronized numerical comparisons: relative velocity, separation, accumulated impulse, and fuel.
4. Add an ordinary-replay condition for evaluation. Keep both interfaces otherwise equivalent.
5. Add optional Bengali explanatory text once the English flow is reviewed.

Prefer these measurable additions before adding VR, motion hardware, real-time AI, or a complex 3D cockpit. The current application requires no human suspension or physical zero-gravity apparatus.

## Week 1 progress-report wording

Use this only after your team has actually reviewed and run the delivered files:

> We reviewed an initial Orbital Lab web prototype covering inertia, rendezvous, and lunar free fall. The current implementation provides prediction prompts, a 2D simulation, live telemetry, and comparison with a second trajectory from the same initial state. We divided the project into learning/research, simulation/validation, and interface/delivery work packages. Numerical checks are included; visual browser checks and learning evaluation remain to be completed. Next week we will finalize the literature comparison, refine the research question, and address issues found on our own devices.

Report your actual tests and changes separately. Do not describe generated starter code, a proposed study, or an unperformed test as work your team independently completed.
