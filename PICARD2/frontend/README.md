# BUBBLE1 PICARD Frontend

Physics-based React frontend where navigation is represented by floating, colliding bubbles.

## Stack

- React + Vite
- react-router-dom
- Tailwind CSS
- matter-js
- framer-motion

## Run

```bash
npm install
npm run dev
```

Create a `.env` file from `.env.example` if your backend is not running at `http://localhost:5000`.

## Build

```bash
npm run build
```

## Key UI Behavior

- Landing page displays floating navigation bubbles.
- Authentication state is restored from the Django session and changes which bubbles are visible.
- Non-landing pages use a single Picard bubble header link back to home.
- Submit page combines static content with a constrained physics area containing action bubbles.
- Accessibility toggle is provided to pause motion and anchor bubbles.

## GitHub OAuth

The frontend starts GitHub sign-in by redirecting the browser to the Django backend at `/auth/github/login/`.

Required frontend env:

```bash
VITE_API_BASE_URL=http://localhost:5000
```

Required backend env:

```bash
FRONTEND_LOCAL_URL=http://localhost:3000
FRONTEND_REMOTE_URL=
GITHUB_OAUTH_LOCAL_CLIENT_ID=
GITHUB_OAUTH_LOCAL_CLIENT_SECRET=
GITHUB_OAUTH_REMOTE_CLIENT_ID=
GITHUB_OAUTH_REMOTE_CLIENT_SECRET=
```

For local development, the GitHub OAuth app callback URL should be `http://localhost:5000/auth/github/callback/`.

## Main Structure

```text
src/
	components/
		auth/
			AuthProvider.jsx
		layout/
			BubbleHeader.jsx
		physics/
			PhysicsWorld.jsx
			BubbleNode.jsx
	pages/
		Landing.jsx
		Submit.jsx
		Experiments.jsx
		Profile.jsx
		About.jsx
```
