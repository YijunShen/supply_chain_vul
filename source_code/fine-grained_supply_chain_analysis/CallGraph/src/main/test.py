from Resolve import Resolve

r = Resolve()

#77676
group = "ro.pippo"
artifact = "pippo-session"
version = "1.11.0"

r.solve_pkg(group, artifact, version, download=True, includedeps=False, depdep=False)
