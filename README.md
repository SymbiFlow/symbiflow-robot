# symbiflow-robot

Simple robot which automates a number of tasks.

Currently they are;
 - Maintain common repository details - [`maintain-repos.py`](./maintain-repos.py);
   - [X] Create the `merge-if-green` label on the repository with color `#00ff00`.
   - [ ] Create the `kokoro:force-run` label on the repository with color `#170e6d`.
   - [X] Make sure all the `triage` team gives `triage` access to all repositories.
   - [ ] Make sure repository has ["Social preview" image](https://help.github.com/en/github/administering-a-repository/customizing-your-repositorys-social-media-preview).

 - Allow developers to add the `merge-if-green` label and;
   - [X] Robot will merge a pull request if Kokoro runs are all green.
   - [ ] TODO: Robot will rerun Kokoro on infra failures?

 - TODO: Maintain common user details;
   - [X] Make sure all committers are also in the `triage` team (FIXME: part of ./maintain-repos.py currently?)

 - Assisting [Depend A Bot generated pull requests](https://dependabot.com/#how-it-works) by;
   - [X] Starting kokoro on new pull requests.
   - [X] Retrying kokoro runs on failures.
   - [X] Merging requests which have all passing kokoro runs.

