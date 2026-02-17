import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { BookOpen, MessageCircle, PenLine, Sparkles } from "lucide-react";

export default function Index() {
  return (
    <div className="max-w-5xl mx-auto px-4">
      {/* Hero */}
      <section className="py-20 md:py-32 text-center space-y-6">
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tight leading-tight" style={{ fontFamily: "var(--font-display)" }}>
          Stories told in<br />
          <span className="text-primary">chapters</span>, shared in<br />
          <span className="text-primary">whispers</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          A calm, beautiful home for serial fiction. Read, write, highlight, and share your favorite passages.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link to="/discover">
            <Button size="lg">Start Reading</Button>
          </Link>
          <Link to="/write">
            <Button variant="outline" size="lg">Start Writing</Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 border-t border-border">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            { icon: BookOpen, title: "Serial Stories", desc: "Publish your stories chapter by chapter. Readers follow along." },
            { icon: MessageCircle, title: "Whispers", desc: "Micro-posts for thoughts, reactions, and quotes from stories." },
            { icon: Sparkles, title: "Highlights", desc: "Select any passage and highlight or whisper about it." },
            { icon: PenLine, title: "Write", desc: "A clean Markdown editor. Focus on your words." },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="space-y-2">
              <Icon className="h-6 w-6 text-primary" />
              <h3 className="font-medium" style={{ fontFamily: "var(--font-display)" }}>{title}</h3>
              <p className="text-sm text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
