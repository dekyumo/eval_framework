import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { Text } from '../ui/Typography';
import type { ConversationTurn } from './types';

interface CaseConversationBuilderProps {
  turns: ConversationTurn[];
  onAddTurn: () => void;
  onRemoveTurn: (index: number) => void;
  onTurnChange: (index: number, field: string, value: string) => void;
  onMediaUpload: (index: number, file: File | null) => void;
}

export function CaseConversationBuilder({
  turns,
  onAddTurn,
  onRemoveTurn,
  onTurnChange,
  onMediaUpload,
}: CaseConversationBuilderProps) {
  return (
    <div className="space-y-4">
      {turns.map((turn, index) => (
        <div key={index} className="flex gap-3" data-testid={`conversation-turn-${index}`}>
          <Select
            fullWidth={false}
            aria-label={index === 0 ? 'Conversation turn role' : `Conversation turn ${index + 1} role`}
            value={turn.role}
            onChange={e => onTurnChange(index, 'role', e.target.value)}
          >
            <option value="user">user</option>
            <option value="assistant">assistant</option>
            <option value="user_media">user_media</option>
          </Select>
          {turn.role === 'user_media' ? (
            <div className="flex-1 space-y-2">
              <input
                type="file"
                accept="image/*,audio/*,video/*"
                aria-label={index === 0 ? 'User media upload' : `User media upload ${index + 1}`}
                data-testid={`user-media-upload-${index}`}
                onChange={e => {
                  void onMediaUpload(index, e.target.files?.[0] || null);
                }}
                className="w-full text-sm text-on-surface file:mr-3 file:rounded-md file:border-0 file:bg-primary-fixed file:px-3 file:py-2 file:text-white"
              />
              {turn.fileName && (
                <Text variant="muted" as="div" className="text-xs">
                  {turn.fileName} ({turn.media_mime})
                </Text>
              )}
              {turn.media_base64 && (
                <span data-testid={`media-ready-${index}`} className="sr-only">media ready</span>
              )}
            </div>
          ) : (
            <Textarea
              className="flex-1 h-20"
              aria-label={index === 0 ? 'User message' : `Conversation turn ${index + 1}`}
              value={turn.content}
              onChange={e => onTurnChange(index, 'content', e.target.value)}
              placeholder="Enter message content..."
            />
          )}
          <Button
            variant="destructive"
            size="sm"
            className="h-10 px-2.5 font-bold"
            onClick={() => onRemoveTurn(index)}
          >
            ×
          </Button>
        </div>
      ))}
      <Button
        variant="ghost"
        size="sm"
        className="text-primary-fixed font-bold"
        onClick={onAddTurn}
      >
        + Add Turn
      </Button>
    </div>
  );
}
