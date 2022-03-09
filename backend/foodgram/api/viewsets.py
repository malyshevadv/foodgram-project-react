from rest_framework import status
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class URLParamNOPayloadViewSet(CreateModelMixin,
                               DestroyModelMixin,
                               GenericViewSet):

    def create_special(self, obj_name, obj_value, usr_value):
        """Метод переопределен:
        POST without payload,
        прописываем поля на основе данных запроса,
        а именно пользователя, отправляющего запрос
        и ID рецепта в адресной строке
        """
        serializer = self.get_serializer(data=self.request.data,
                                         context={
                                             obj_name: obj_value,
                                             'user': usr_value})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def get_serializer(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        передаем корректный контекст для сериалайзера
        """
        serializer_class = self.get_serializer_class()

        draft_request_data = self.request.data.copy()
        for key, value in kwargs['context'].items():
            draft_request_data[key] = value

        kwargs['context'] = self.get_serializer_context()
        # kwargs['data'] immutable - поэтому заменяем
        kwargs['data'] = draft_request_data
        return serializer_class(*args, **kwargs)

    def delete_special(self, queryset):
        if queryset.count() == 1:
            queryset.first().delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        if queryset.count() == 0:
            return Response(
                'Ошибка удаления объекта: не найдено.',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            'Ошибка удаления объекта: что-то пошло не так.',
            status=status.HTTP_400_BAD_REQUEST
        )
