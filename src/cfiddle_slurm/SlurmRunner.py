

class SlurmRunnerDelegate:
    
    def execute(self, command, runner):

        libs_to_take = self._collect_libs(runner) # need this to execute
        source_to_take = self._collect_source(runner) # take this for AI violation checking.
        
        command[0] = "cse142l-cfiddle-run"
        cse142l_command = ["cse142",  "job", "run", "--force", "--lab", os.environ["CSE142L_LAB"], *source_to_take,  *libs_to_take, "--take", "short_name",  "--take", ".cfiddle/**/*.pickle", " ".join(command)]
        try:
            #log.warn(f"Executing: {' '.join(cse142l_command)}")
            subprocess.run(cse142l_command, check=True)
        except subprocess.CalledProcessError as e:
            raise RunnerDelegateException(f"CSE142L_RunnerDelegate failed (error code {e.returncode}): Command: {' '.join (cse142l_command)}\nstdout: {e.stdout}\n stderr: {e.stderr}")

        
    def _collect_libs(self, runner):
        dot_so_files = set()

        for invocation in runner.get_invocations():
            dot_so_files.add(invocation.executable.lib)
            
        return self._render_take(dot_so_files)

    def _collect_source(self, runner):
        files = set()

        for invocation in runner.get_invocations():
            files.add(invocation.executable.build_spec.source_file)
            
        return self._render_take(files)

    def _render_take(self, l):
        return sum([["--take", so] for so in l], [])
        
