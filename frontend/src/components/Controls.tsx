'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface ControlsProps {
  k: number;
  onKChange: (k: number) => void;
  useMmr: boolean;
  onMmrChange: (useMmr: boolean) => void;
  similarityMethod: string;
  onSimilarityChange: (method: string) => void;
}

export function Controls({
  k,
  onKChange,
  useMmr,
  onMmrChange,
  similarityMethod,
  onSimilarityChange,
}: ControlsProps) {
  return (
    <div className="flex flex-wrap gap-4 items-center">
      <div className="flex items-center space-x-2">
        <Label htmlFor="k-select">結果数:</Label>
        <Select value={k.toString()} onValueChange={(value) => onKChange(parseInt(value))}>
          <SelectTrigger id="k-select" className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">1</SelectItem>
            <SelectItem value="3">3</SelectItem>
            <SelectItem value="5">5</SelectItem>
            <SelectItem value="10">10</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="mmr-switch"
          checked={useMmr}
          onCheckedChange={onMmrChange}
        />
        <Label htmlFor="mmr-switch">MMR</Label>
      </div>

      <div className="flex items-center space-x-2">
        <Label htmlFor="similarity-select">類似度:</Label>
        <Select value={similarityMethod} onValueChange={onSimilarityChange}>
          <SelectTrigger id="similarity-select" className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="distance">Distance</SelectItem>
            <SelectItem value="dot">Dot</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
