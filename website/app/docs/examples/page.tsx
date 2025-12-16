import { BookOpen } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'Examples',
  description: 'Code examples and tutorials for using the Mizan API',
};

export default function ExamplesPage() {
  return (
    <ComingSoon
      title="Code Examples"
      description="Practical examples in Python, JavaScript, and other languages showing how to integrate Mizan API into your applications. From basic letter counting to advanced Abjad analysis."
      icon={<BookOpen className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
