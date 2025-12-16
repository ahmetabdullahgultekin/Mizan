import { Users } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'Contributing',
  description: 'Guidelines for contributing to the Mizan project',
};

export default function ContributingPage() {
  return (
    <ComingSoon
      title="Contributing Guide"
      description="Learn how to contribute to Mizan. From reporting bugs to submitting pull requests, we welcome all contributions that align with our scholarly standards and code of conduct."
      icon={<Users className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
