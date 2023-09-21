import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay
import graphql_jwt
from graphql_jwt.decorators import login_required

from accounts.models import CustomUser
from posts.models import Post

class AccountType(DjangoObjectType):
    class Meta:
        model = CustomUser
        #fields = "__all__"
        exclude = ('password',)

    def resolve_post(self, info):
        return Post.objects.filter(author=self)
    
    @classmethod
    def get_node(cls, self, id):
        return AccountType.objects.get(id=id)


class PostType(DjangoObjectType):
    class Meta:
        model = Post
        filter_fields = {'title':['exact', 'icontains', 'istartswith']}
        fields = "__all__"
        interfaces = (relay.Node, )


class Query(graphene.ObjectType):
    all_accounts = graphene.List(AccountType)
    logged_in_user = graphene.Field(AccountType)
    filter_posts = DjangoFilterConnectionField(PostType)
    all_posts = graphene.List(PostType)
    post = graphene.Field(PostType, post_id=graphene.Int())

    def resolve_authors(self, info):
        return CustomUser.objects.all()

    @login_required
    def resolve_logged_in_user(self, info):
        return info.context.user

    @login_required
    def resolve_all_posts(self, info, **kwargs):
        return Post.objects.all()

    def resolve_post(self, info, post_id):
        return Post.objects.get(pk=post_id)


class UserInput(graphene.InputObjectType):
    id = graphene.ID()
    email = graphene.String()
    username = graphene.String()
    password = graphene.String()


class CreateUser(graphene.Mutation):
    class Arguments:
        user_data = UserInput(required=True)
    
    user = graphene.Field(AccountType)

    @staticmethod
    def mutate(self, info, user_data=None):
        user_instance = CustomUser( 
            email=user_data.email,
            username=user_data.username,
        )
        user_instance.set_password(user_data.password)
        user_instance.save()

        return CreateUser(user=user_instance)



class PostInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String()
    body = graphene.String()
    author = graphene.ID()


class CreatePost(graphene.Mutation):
    class Arguments:
        post_data = PostInput(required=True)

    post = graphene.Field(PostType)

    @staticmethod
    def mutate(root, info, post_data=None):
        author = CustomUser.objects.get(pk=post_data.author)
        post_instance = Post( 
            title=post_data.title,
            author=author,
            body=post_data.body,
        )
        post_instance.save()
        return CreatePost(post=post_instance)





class UpdatePost(graphene.Mutation):
    class Arguments:
        post_data = PostInput(required=True)

    post = graphene.Field(PostType)

    @staticmethod
    def mutate(root, info, post_data=None):
        try:
            # Attempt to retrieve the Post instance by ID
            post_instance = Post.objects.get(pk=post_data.id)
            author = CustomUser.objects.get(pk=post_data.author)
            # Update the fields if the Post instance exists
            post_instance.title = post_data.title
            post_instance.author = author
            post_instance.body = post_data.body
            post_instance.save()

            return UpdatePost(post=post_instance)

        except Post.DoesNotExist:
            # Handle the case where the specified post doesn't exist
            return UpdatePost(post=None)




class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    post = graphene.Field(PostType)

    @staticmethod
    def mutate(root, info, id):
        post_instance = Post.objects.get(pk=id)
        post_instance.delete()

        return None


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)