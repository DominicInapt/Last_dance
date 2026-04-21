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

## Build

```bash
npm run build
```

## Key UI Behavior

- Landing page displays floating navigation bubbles.
- Authentication state changes which bubbles are visible.
- Non-landing pages use a single Picard bubble header link back to home.
- Submit page combines static content with a constrained physics area containing action bubbles.
- Accessibility toggle is provided to pause motion and anchor bubbles.

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
