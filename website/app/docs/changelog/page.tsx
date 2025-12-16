import { History } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'Changelog',
  description: 'Version history and release notes for Mizan',
};

export default function ChangelogPage() {
  return (
    <ComingSoon
      title="Changelog"
      description="Track all changes, improvements, and bug fixes across Mizan versions. Stay updated with our development progress and upcoming features."
      icon={<History className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
