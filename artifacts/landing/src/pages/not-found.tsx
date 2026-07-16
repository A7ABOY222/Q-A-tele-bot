import { Link, Route } from "wouter";

export default function NotFound() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background">
      <div className="text-center p-8 bg-card border border-border rounded-2xl shadow-xl max-w-md w-full">
        <h1 className="text-6xl font-black font-serif text-gradient mb-4">404</h1>
        <h2 className="text-2xl font-bold mb-4">Page Not Found</h2>
        <p className="text-muted-foreground mb-8">
          The page you are looking for doesn't exist or has been moved.
        </p>
        <Link 
          href="/"
          className="inline-flex items-center justify-center px-6 py-3 rounded-full bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}