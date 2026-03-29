import Link from "next/link";
import { GradientDots } from "@/components/ui/gradient-dots";

export default function Home() {
  return (
    <main className="relative flex min-h-screen w-full flex-col items-center justify-center overflow-hidden px-4">
      <GradientDots duration={20} />
      <div className="z-10 max-w-lg text-center">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl">
          Grafana → Kibana
        </h1>
        <p className="mt-4 text-muted-foreground">
          Next.js + shadcn UI shell. The converter UI is served by the FastAPI app
          (e.g. local <code className="rounded bg-muted px-1 py-0.5 text-sm">python main.py</code>
          ).
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href="/demo"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Gradient dots demo
          </Link>
        </div>
      </div>
    </main>
  );
}
