import LcarsLayout from '../components/layout/LcarsLayout'

export default function About() {
  return (
    <LcarsLayout>
      <section className="panel-card panel-card-accent">
        <p className="lcars-eyebrow">Platform Brief</p>
        <h1>About the PICARD LCARS frontend</h1>
        <p className="lead-copy">
          This interface replaces the previous physics-driven prototype with an LCARS-styled command deck
          that exposes the actual Django, Celery, and Spark workflows present in the repository.
        </p>
      </section>

      <section className="panel-grid two-up">
        <article className="panel-card">
          <p className="lcars-eyebrow">Capabilities</p>
          <h2>Supported operations</h2>
          <ul className="stack-list">
            <li>GitHub-only sign-in, backed by Django session authentication.</li>
            <li>CSV dataset uploads with private and public visibility controls.</li>
            <li>Python and JAR algorithm uploads, including JAR main class support.</li>
            <li>Experiment creation, queueing, re-running, deletion, and result inspection.</li>
          </ul>
        </article>

        <article className="panel-card">
          <p className="lcars-eyebrow">Runtime Path</p>
          <h2>How requests flow</h2>
          <ul className="stack-list">
            <li>The frontend proxies backend routes through the deployment origin for cleaner OAuth and cookies.</li>
            <li>Django stores datasets and scripts, constructs experiment records, and serves session state.</li>
            <li>Celery triggers Spark submissions and appends live output back onto experiment records.</li>
            <li>Saved result files become downloadable from the experiment detail console.</li>
          </ul>
        </article>
      </section>

      <section className="panel-card">
        <p className="lcars-eyebrow">Constraints</p>
        <h2>Current repository limits</h2>
        <ul className="stack-list">
          <li>Authentication currently enforces membership in ThePICARDProject.</li>
          <li>The backend API now includes delete and result download endpoints needed by the frontend.</li>
          <li>Django migrations for datasets, scripts, and experiments were added to the repository in this pass.</li>
          <li>Accessibility targets a keyboard and screen-reader baseline while retaining optional LCARS sound cues.</li>
        </ul>
      </section>
    </LcarsLayout>
  )
}
