# Live narration · 2 minutes 30 seconds

<!-- covers: presentation/src/index.tsx -->

**00:00–00:14 · Better deals. Every move explained.**
We built Haggle: an autonomous procurement negotiator. In our latest full practice run, it closed ten deals at a mean arena score of 77.2%, reducing modeled total cost by €1.17 million. These are simulation results.

**00:14–00:30 · The sprint.**
Over one hackathon night, we moved from an inspectable negotiation page to a general agent, an economics engine and a resilient final runner. The repo holds 312 run records, including agent runs and scripted probes. Each experiment helped us inspect what suppliers actually responded to.

**00:30–00:50 · The core idea.**
Our most important design decision was to give code ownership of the numbers. It computes verified facts, evaluates total cost and creates a menu of equally valuable packages. The model reads the supplier’s priorities, selects a package and writes the email. Different terms can create value for the supplier without costing us more.

**00:50–01:08 · Measured impact.**
Across the same ten cases, opening offers cost €12.76 million in the arena’s model. Negotiated deals cost €11.59 million: a 9.2% reduction. This accounts for more than the sticker price—payment, risk and supply terms matter. It is modeled value, not money already saved in a business.

**01:08–01:28 · The surprising deal.**
One supplier accepted a higher unit price with longer payment terms. That sounds worse until you value the cash. The observed score rose from 65.9 to 73.5%. The lesson is simple: optimize the whole deal. A price-only agent would miss this trade.

**01:28–01:46 · The scorecard.**
All ten cases ended in deals. Renewals were strong; raw-material cases were harder. This gives us a precise improvement map. Our complete-suite snapshots rose from 65.3 to 77.2%, though changed policies and supplier variability mean we cannot attribute that gain to one feature.

**01:46–02:04 · What failed.**
We tested pressure, anchors, rival claims and term changes. Some ideas failed. Eight morning experiments produced no measured gain, and we reverted the wrong levers. Verified evidence and sound deal structure mattered more than clever wording. Our process preserves failures as evidence, too.

**02:04–02:20 · Built for failure.**
We also rehearsed the final with every model call broken. Across five waves and fifty offline cases, forty-five became deals and five took the alternative. None remained unresolved. That validates graceful completion under model failure; hosted final performance still needs to be measured.

**02:20–02:30 · Close.**
Haggle combines a general negotiating agent, an auditable economics engine and an experiment-driven development process. Our takeaway: negotiate with evidence, and optimize the whole deal.
