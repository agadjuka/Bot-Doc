# Настройка SERVICE_URL для Cloud Run

## Проблема

В логах видно предупреждение:
```
⚠️ SERVICE_URL не установлен - keep-alive отключен
```

Это происходит потому, что Google Cloud Run не автоматически устанавливает переменную `SERVICE_URL`. Keep-alive механизм не может работать без знания собственного URL.

## Решение

### Вариант 1: Автоматическое определение URL (рекомендуется)

Код теперь автоматически пытается определить URL сервиса из стандартных переменных Cloud Run:

```python
def get_service_url():
    # Проверяем SERVICE_URL (если установлен вручную)
    service_url = os.getenv("SERVICE_URL")
    if service_url:
        return service_url
    
    # Автоматически строим URL из переменных Cloud Run
    region = os.getenv("K_REGION", "us-central1")
    service_name = os.getenv("K_SERVICE")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    if service_name and project_id:
        return f"https://{service_name}-{project_id}.{region}.run.app"
    
    return None
```

### Вариант 2: Ручная установка SERVICE_URL

Если автоматическое определение не работает, установите переменную вручную:

#### Через Google Cloud Console:

1. Откройте [Google Cloud Console](https://console.cloud.google.com/)
2. Перейдите в **Cloud Run**
3. Выберите ваш сервис `ai-bot`
4. Нажмите **"Edit & Deploy New Revision"**
5. Перейдите на вкладку **"Variables & Secrets"**
6. Добавьте переменную:
   - **Name**: `SERVICE_URL`
   - **Value**: `https://ai-bot-366461711404.asia-southeast1.run.app`

#### Через gcloud CLI:

```bash
gcloud run services update ai-bot \
  --region=asia-southeast1 \
  --set-env-vars="SERVICE_URL=https://ai-bot-366461711404.asia-southeast1.run.app"
```

#### Через cloudbuild.yaml:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'ai-bot'
      - '--image'
      - 'gcr.io/$PROJECT_ID/ai-bot'
      - '--region'
      - 'asia-southeast1'
      - '--set-env-vars'
      - 'SERVICE_URL=https://ai-bot-366461711404.asia-southeast1.run.app'
```

## Проверка

После настройки в логах должно появиться:

```
💓 Starting keep-alive ping to https://ai-bot-366461711404.asia-southeast1.run.app
💓 Keep-alive ping sent successfully.
```

## Отладка

Если keep-alive все еще не работает, проверьте переменные окружения:

```bash
# Проверка через Cloud Console или gcloud
gcloud run services describe ai-bot --region=asia-southeast1 --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

Или используйте эндпоинт `/debug` для проверки:

```bash
curl https://ai-bot-366461711404.asia-southeast1.run.app/debug
```

## Важные замечания

1. **URL должен быть точным**: Используйте полный URL с `https://`
2. **Регион важен**: Убедитесь, что регион в URL соответствует региону сервиса
3. **Автоматическое определение**: Код теперь пытается определить URL автоматически, но ручная установка более надежна
4. **Без keep-alive**: Без этой настройки контейнер может "засыпать" при отсутствии трафика

## Результат

После правильной настройки:
- ✅ Keep-alive будет работать автоматически
- ✅ Контейнер не будет "засыпать"
- ✅ Не будет "холодного старта" при новых запросах
- ✅ В логах будут появляться сообщения о успешных пингах каждые 5 минут
