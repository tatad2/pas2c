int x, y;
int z[101][201][301];
int z[101];
int __func_gcd(int& a,int& b) {
	int gcd;
	if(b==0) {
		gcd=a;
	}
	else {
		gcd=__func_gcd(a,b);
	}
	return gcd;
}
int main() {
	scanf("%d%d", x, y);
	z[x][150][300]=x;
	__func_gcd(x,y);
	printf("%d\n", __func_gcd(x,y));
	return 0;
}
