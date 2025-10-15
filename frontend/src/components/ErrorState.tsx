'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

interface ErrorStateProps {
  error: Error;
  onRetry: () => void;
}

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const getErrorMessage = (error: Error) => {
    if (error.message.includes('422')) {
      return 'クエリが空です';
    }
    if (error.message.includes('429')) {
      return 'サーバーが混雑しています。少し待ってから再試行してください';
    }
    if (error.message.includes('5')) {
      return 'サーバーエラーが発生しました。しばらく待ってから再試行してください';
    }
    return '検索中にエラーが発生しました';
  };

  return (
    <Card className="border-destructive">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold text-destructive">エラーが発生しました</h3>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground mb-4">
          {getErrorMessage(error)}
        </p>
        <Button onClick={onRetry} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          再試行
        </Button>
      </CardContent>
    </Card>
  );
}
